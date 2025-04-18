import os
import Metashape
import time
import logging
from pipeline.utils import setup_logger, move_file, move_all_files, remove_lockfile
from datetime import datetime

class MetashapeProject:
    """
    Handles the creation and management of a Metashape project.
    
    Attributes:
        project_path (str): Path to the Metashape project file.
        doc (Metashape.Document): The Metashape project document object.
    """
    def __init__(self, project_path):
        """
        Initializes a Metashape project and sets the project path.
        
        Args:
            project_path (str): Path to the Metashape project file.
        """
        self.doc = Metashape.Document()
        self.project_path = project_path

    def save(self):
        """
        Saves the current project and removes any lock files, ensuring the project is saved without interruption.
        """
        remove_lockfile(self.project_path)
        self.doc.save(self.project_path)
        time.sleep(5)  # Wait to ensure the save completes properly
        remove_lockfile(self.project_path)

    def add_chunk(self, chunk_name, image_list):
        """
        Adds a chunk to the project and loads the provided images.
        
        Args:
            chunk_name (str): Name of the chunk to be added.
            image_list (list): List of image paths to be loaded into the chunk.

        Returns:
            Metashape.Chunk: The newly created chunk with loaded images.
        """
        chunk = self.doc.addChunk()
        chunk.label = chunk_name
        chunk.addPhotos(image_list, load_xmp_accuracy=True, load_rpc_txt=True)
        logging.info(f"{len(chunk.cameras)} images loaded in chunk: {chunk_name}")
        return chunk

class MetashapeChunkProcessor:
    """
    Processes a Metashape chunk, handling various stages of processing such as aligning photos,
    building point clouds, and generating orthomosaics.
    
    Attributes:
        chunk (Metashape.Chunk): The chunk to be processed.
    """
    def __init__(self, chunk):
        """
        Initializes the processor for a given chunk.
        
        Args:
            chunk (Metashape.Chunk): The chunk to be processed.
        """
        self.chunk = chunk

    def align_photos(self):
        """
        Aligns the photos in the chunk by matching tie points and aligning cameras.
        """
        logging.info(f"Aligning photos for chunk: {self.chunk.label}")
        self.chunk.matchPhotos(downscale=1,reference_preselection=True,keypoint_limit=60000,tiepoint_limit=15000,filter_mask=False,guided_matching=True,mask_tiepoints=False)
        self.chunk.alignCameras()

    def build_depth_maps(self):
        """
        Builds depth maps for the chunk.
        """
        logging.info(f"Building Depth Maps for chunk: {self.chunk.label}")
        self.chunk.buildDepthMaps(downscale=2, filter_mode=Metashape.MildFiltering)

    def build_point_cloud(self):
        """
        Builds a point cloud from the depth maps.
        """
        logging.info(f"Building point cloud for chunk: {self.chunk.label}")
        self.chunk.buildPointCloud()

    def build_model(self):
        """
        Builds a 3D model from the point cloud.
        """
        logging.info(f"Building model for chunk: {self.chunk.label}")
        self.chunk.buildModel(source_data=Metashape.DepthMapsData)

    def smooth_model(self):
        """
        Applies smoothing to the 3D model.
        """
        logging.info(f"Smoothing model for chunk: {self.chunk.label}")
        self.chunk.smoothModel(strength=6)

    def build_orthomosaic(self):
        """
        Builds an orthomosaic from the 3D model.
        """
        logging.info(f"Building orthomosaic for chunk: {self.chunk.label}")
        self.chunk.buildOrthomosaic(surface_data=Metashape.DataSource.ModelData)

    def export_raster(self, export_folder):
        """
        Exports the orthomosaic as a raster image to the specified folder.
        
        Args:
            export_folder (str): The folder where the orthomosaic will be saved.
        """
        ortho_path = os.path.join(export_folder, f"{self.chunk.label}_orthomosaic.tif")

        compression = Metashape.ImageCompression()
        compression.tiff_compression = Metashape.ImageCompression.TiffCompressionLZW
        compression.jpeg_quality = 90
        compression.tiff_big = True
        compression.tiff_overviews = True
        compression.tiff_tiled = True

        out_projection = Metashape.OrthoProjection()
        out_projection.type = Metashape.OrthoProjection.Type.Planar
        out_projection.crs = Metashape.CoordinateSystem("EPSG::4326")

        self.chunk.exportRaster(path=ortho_path,
                                source_data=Metashape.OrthomosaicData,
                                image_compression=compression,
                                save_alpha=True,
                                white_background=True,
                                projection=out_projection)

        logging.info(f"Exported orthomosaic to {ortho_path}")

class MetashapeProcessor:
    """
    Main processor for handling the execution of Metashape processing tasks.
    
    Attributes:
        input_folder (str): Folder containing the project data.
        gpu_option (str): Specifies which GPU to use ('0', '1', or 'all').
        cpu_enabled (bool): Whether CPU processing is enabled.
        tmp_folder (str): Temporary folder for intermediate files.
        log_file (str): Path to the log file for recording processing information.
    """
    def __init__(self, config, log_file):
        """
        Initializes the processor with the given configuration and log file.
        
        Args:
            config (dict): Configuration dictionary containing input_folder, gpu_option, etc.
            log_file (str): Path to the log file.
        """
        self.input_folder = config["input_folder"]
        self.gpu_option = config["gpu_option"]
        self.cpu_enabled = config["cpu_enabled"]
        self.tmp_folder = config["tmp_folder"]
        self.log_file = log_file

        # Set up logging
        self.logger = setup_logger(self.log_file)

        # Configure GPUs based on the user's choice
        if self.gpu_option == 'all':
            self.logger.info("Using both GPUs (0 and 1).")
            Metashape.app.gpu_mask = (1 << 0) | (1 << 1)  # Enable GPU 0 and GPU 1
        elif self.gpu_option == '0':
            os.environ["CUDA_VISIBLE_DEVICES"] = "0"
            self.logger.info("Using GPU 0 only.")
            Metashape.app.gpu_mask = 1 << 0  # Enable only GPU 0
        elif self.gpu_option == '1':
            os.environ["CUDA_VISIBLE_DEVICES"] = "1"
            self.logger.info("Using GPU 1 only.")
            Metashape.app.gpu_mask = 1 << 1  # Enable only GPU 1
        else:
            raise ValueError("Invalid GPU option. Use '0', '1', or 'all'.")

        # Optionally enable or disable CPU processing
        Metashape.app.cpu_enable = self.cpu_enabled
        self.logger.info(f"CPU enabled: {self.cpu_enabled}")

    def process_folders(self):
        """
        Processes all folders in the input directory that contain unprocessed data.
        """
        for folder_name in sorted(os.listdir(self.input_folder)):
            folder_path = os.path.join(self.input_folder, folder_name)
            if os.path.isdir(folder_path) and "_unprocessed" in folder_name:
                self.process_unprocessed_folder(folder_path)
        
        # Force log flush
        logging.shutdown()

    def process_unprocessed_folder(self, folder_path):
        """
        Processes an unprocessed folder, including image loading, model generation, and exporting results.
        
        Args:
            folder_path (str): Path to the folder to be processed.
        """
        self.logger.info(f"Processing folder: {folder_path}")
        
        # Create a temporary folder for processing
        base_dir = os.path.basename(os.path.normpath(folder_path))
        tmp_project_folder = os.path.join(self.tmp_folder, base_dir)
        os.makedirs(tmp_project_folder, exist_ok=True)

        # Create an export directory inside the _unprocessed folder
        export_folder = os.path.join(tmp_project_folder, "export")
        os.makedirs(export_folder, exist_ok=True)

        # Define the path for the project file
        project_path = os.path.join(tmp_project_folder, "project.psx")
        project = MetashapeProject(project_path)
        project.save()

        # Locate the "photos" directory within the "_unprocessed" folder
        photos_dir = os.path.join(folder_path, "photos")
        if os.path.isdir(photos_dir):
            for subfolder_name in sorted(os.listdir(photos_dir)):
                subfolder_path = os.path.join(photos_dir, subfolder_name)
                if os.path.isdir(subfolder_path):
                    self.logger.info("Processing RGB and multispectral images by their specific naming convention")
                    image_dict = {
                        "RGB": [os.path.join(subfolder_path, file_name) for file_name in os.listdir(subfolder_path) if file_name.endswith(".JPG")],
                        "NIR": [os.path.join(subfolder_path, file_name) for file_name in os.listdir(subfolder_path) if file_name.endswith("MS_NIR.TIF")],
                        "RE": [os.path.join(subfolder_path, file_name) for file_name in os.listdir(subfolder_path) if file_name.endswith("MS_RE.TIF")],
                        "R": [os.path.join(subfolder_path, file_name) for file_name in os.listdir(subfolder_path) if file_name.endswith("MS_R.TIF")],
                        "G": [os.path.join(subfolder_path, file_name) for file_name in os.listdir(subfolder_path) if file_name.endswith("MS_G.TIF")],
                    }

                    for channel, image_list in image_dict.items():
                        try:
                            if not image_list:
                                continue
                            
                            self.logger.info(f"Adding {channel} photos to chunk: {subfolder_name}_{channel}")
                            chunk_name = f"{subfolder_name}_{channel}"
                            chunk = project.add_chunk(chunk_name, image_list)
                            processor = MetashapeChunkProcessor(chunk)

                            processor.align_photos()
                            project.save()

                            processor.build_depth_maps()
                            project.save()

                            processor.build_model()
                            project.save()

                            has_transform = chunk.transform.scale and chunk.transform.rotation and chunk.transform.translation

                            if has_transform:
                                processor.build_point_cloud()
                                project.save()

                                processor.smooth_model()
                                project.save()

                                processor.build_orthomosaic()
                                project.save()

                            processor.export_raster(export_folder)
                            project.save()
                        except Exception as e:
                            self.logger.error(f"Error processing chunk {subfolder_name}_{channel}: {str(e)}")
                            pass

        try:
            move_all_files(tmp_project_folder, folder_path)
            move_file(self.log_file, folder_path)

            processed_folder = folder_path.replace("_unprocessed", "_processed")
            os.rename(folder_path, processed_folder)
            self.logger.info(f"Renamed folder to: {processed_folder}")
        except Exception as e:
            self.logger.error(f"Error handling files or renaming folder: {str(e)}")
            pass
