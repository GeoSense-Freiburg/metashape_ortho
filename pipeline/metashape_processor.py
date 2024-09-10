import os
import Metashape
import logging
from pipeline.utils import print_timestamp, setup_logger, move_file
from datetime import datetime

class MetashapeProject:
    def __init__(self, project_path):
        self.doc = Metashape.Document()
        self.project_path = project_path

    def save(self):
        self.doc.save(self.project_path)

    def add_chunk(self, chunk_name, image_list):
        chunk = self.doc.addChunk()
        chunk.label = chunk_name
        chunk.addPhotos(image_list, load_xmp_accuracy=True, load_rpc_txt=True)
        logging.info(f"{len(chunk.cameras)} images loaded in chunk: {chunk_name}")
        return chunk

class MetashapeChunkProcessor:
    def __init__(self, chunk):
        self.chunk = chunk

    def align_photos(self):
        logging.info(f"Aligning photos for chunk: {self.chunk.label}")
        self.chunk.matchPhotos(downscale=0, mask_tiepoints=False)
        self.chunk.alignCameras()

    def build_depth_maps(self):
        logging.info(f"Building Depth Maps for chunk: {self.chunk.label}")
        self.chunk.buildDepthMaps(downscale=2, filter_mode=Metashape.MildFiltering)

    def build_point_cloud(self):
        logging.info(f"Building point cloud for chunk: {self.chunk.label}")
        self.chunk.buildPointCloud()

    def build_model(self):
        logging.info(f"Building model for chunk: {self.chunk.label}")
        self.chunk.buildModel(source_data=Metashape.DepthMapsData)

    def smooth_model(self):
        logging.info(f"Smoothing model for chunk: {self.chunk.label}")
        self.chunk.smoothModel(strength=6)

    def build_orthomosaic(self):
        logging.info(f"Building orthomosaic for chunk: {self.chunk.label}")
        self.chunk.buildOrthomosaic(surface_data=Metashape.DataSource.ModelData)

    def export_raster(self, export_folder):
        ortho_path_tmp = f"/tmp/tmp_orthos/{self.chunk.label}_orthomosaic.tif"
        ortho_path = os.path.join(export_folder, f"{self.chunk.label}_orthomosaic.tif")

        compression = Metashape.ImageCompression()
        compression.tiff_compression = Metashape.ImageCompression.TiffCompressionJPEG
        compression.jpeg_quality = 90
        compression.tiff_big = True
        compression.tiff_overviews = True
        compression.tiff_tiled = True

        out_projection = Metashape.OrthoProjection()
        out_projection.type = Metashape.OrthoProjection.Type.Planar
        out_projection.crs = Metashape.CoordinateSystem("EPSG::4326")

        self.chunk.exportRaster(path=ortho_path_tmp,
                                source_data=Metashape.OrthomosaicData,
                                image_compression=compression,
                                save_alpha=False,
                                white_background=True,
                                projection=out_projection)

        logging.info(f"Exported orthomosaic to {ortho_path_tmp}")
        move_file(ortho_path_tmp, ortho_path)

class MetashapeProcessor:
    def __init__(self, input_folder, log_file, gpu_option, cpu_enabled):
        self.input_folder = input_folder
        self.gpu_option = gpu_option
        self.cpu_enabled = cpu_enabled

        # Set up logging
        self.logger = setup_logger(log_file)

        # Configure GPUs based on the user's choice
        if self.gpu_option == 'both':
            logging.info("Using both GPUs (0 and 1).")
            Metashape.app.gpu_mask = (1 << 0) | (1 << 1)  # Enable GPU 0 and GPU 1
        elif self.gpu_option == '0':
            logging.info("Using GPU 0 only.")
            Metashape.app.gpu_mask = 1 << 0  # Enable only GPU 0
        elif self.gpu_option == '1':
            logging.info("Using GPU 1 only.")
            Metashape.app.gpu_mask = 1 << 1  # Enable only GPU 1
        else:
            raise ValueError("Invalid GPU option. Use '0', '1', or 'both'.")

        # Optionally enable or disable CPU processing
        Metashape.app.cpu_enable = self.cpu_enabled
        logging.info(f"CPU enabled: {self.cpu_enabled}")

    def process_folders(self):
        for folder_name in sorted(os.listdir(self.input_folder)):
            folder_path = os.path.join(self.input_folder, folder_name)
            if os.path.isdir(folder_path) and "_unprocessed" in folder_name:
                self.process_unprocessed_folder(folder_path)

    def process_unprocessed_folder(self, folder_path):
        logging.info(f"Processing folder: {folder_path}")
        
        # Create an export directory inside the _unprocessed folder
        export_folder = os.path.join(folder_path, "export")
        os.makedirs(export_folder, exist_ok=True)

        # Define the path for the project file
        project_path = os.path.join(folder_path, "project.psx")
        project = MetashapeProject(project_path)
        project.save()

        # Locate the "photos" directory within the "_unprocessed" folder
        photos_dir = os.path.join(folder_path, "photos")
        if os.path.isdir(photos_dir):
            for subfolder_name in sorted(os.listdir(photos_dir)):
                subfolder_path = os.path.join(photos_dir, subfolder_name)
                if os.path.isdir(subfolder_path):
                    image_list = [os.path.join(subfolder_path, file_name) for file_name in os.listdir(subfolder_path) if file_name.lower().endswith(".jpg")]
                    if not image_list:
                        continue
                    
                    logging.info(f"Adding photos to chunk: {subfolder_name}")
                    print_timestamp()
                    chunk = project.add_chunk(subfolder_name, image_list)
                    processor = MetashapeChunkProcessor(chunk)

                    print_timestamp()
                    processor.align_photos()
                    project.save()

                    print_timestamp()
                    processor.build_depth_maps()
                    project.save()

                    print_timestamp()
                    processor.build_model()
                    project.save()

                    has_transform = chunk.transform.scale and chunk.transform.rotation and chunk.transform.translation

                    if has_transform:
                        print_timestamp()
                        processor.build_point_cloud()
                        project.save()

                        print_timestamp()
                        processor.smooth_model()
                        project.save()

                        print_timestamp()
                        processor.build_orthomosaic()
                        project.save()

                    # Export all desired files
                    print_timestamp()
                    processor.export_raster(export_folder)
                    project.save()
                    
        # Rename the processed folder from _unprocessed to _processed
        processed_folder = folder_path.replace("_unprocessed", "_processed")
        os.rename(folder_path, processed_folder)
        logging.info(f"Renamed folder to: {processed_folder}")
