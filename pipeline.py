import os
import sys
from datetime import datetime
# Metashape should be installed in your local environment (best with python 3.9)
# follow: https://agisoft.freshdesk.com/support/solutions/articles/31000148930-how-to-install-metashape-stand-alone-python-module
import Metashape
# https://www.agisoft.com/pdf/metashape_python_api_2_1_2.pdf
import shutil

# Checking compatibility
compatible_major_version = "2.1"
found_major_version = ".".join(Metashape.app.version.split('.')[:2])
if found_major_version != compatible_major_version:
    raise Exception("Incompatible Metashape version: {} != {}".format(found_major_version, compatible_major_version))

# <?xml version="1.0" encoding="UTF-8"?>
# <batchjobs version="2.1.1" save_project="true">
#   <job name="AlignPhotos" target="all">
#     <downscale>0</downscale>
#     <mask_tiepoints>false</mask_tiepoints>
#   </job>
#   <job name="BuildPointCloud" target="all">
#     <downscale>2</downscale>
#     <reuse_depth>true</reuse_depth>
#   </job>
#   <job name="BuildModel" target="all">
#     <reuse_depth>true</reuse_depth>
#     <source_data>1</source_data>
#     <surface_type>1</surface_type>
#   </job>
#   <job name="SmoothModel" target="all">
#     <strength>6</strength>
#   </job>
#   <job name="BuildOrthomosaic" target="all">
#     <projection>
#       <crs>GEOGCS["WGS 84",DATUM["World Geodetic System 1984 ensemble",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],TOWGS84[0,0,0,0,0,0,0],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.01745329251994328,AUTHORITY["EPSG","9102"]],AUTHORITY["EPSG","4326"]]</crs>
#       <transform>1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1</transform>
#       <surface>0</surface>
#       <radius>1</radius>
#     </projection>
#   </job>
#   <job name="ExportOrthomosaic" target="all">
#     <image_format>2</image_format>
#     <path>{projectfolder}/{chunklabel}.tif</path>
#   </job>
# </batchjobs>

# global functions
def move_file(source_path, destination_path):
        try:
            # Move the file from source_path to destination_path
            shutil.move(source_path, destination_path)
            print(f"File moved successfully from {source_path} to {destination_path}")
        except Exception as e:
            print(f"Error moving file: {e}")


# metashape project
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
        print(str(len(chunk.cameras)) + " images loaded")
        return chunk
    
    def close(self):
        # Save the project before closing
        self.doc.save()
        # Close the project
        self.doc.close()
        print(f"Project at {self.project_path} has been closed successfully.")

class MetashapeChunkProcessor:
    def __init__(self, chunk):
        self.chunk = chunk

    def align_photos(self):
        print(f"\n----\nAligning photos for chunk: {self.chunk.label}")
        self.chunk.matchPhotos(downscale=0, mask_tiepoints=False)
        self.chunk.alignCameras()

    def build_depth_maps(self):
        print(f"\n----\nBuilding Depth Maps for chunk: {self.chunk.label}")
        self.chunk.buildDepthMaps(downscale = 2, filter_mode = Metashape.MildFiltering)

    def build_point_cloud(self):
        print(f"\n----\nBuilding point cloud for chunk: {self.chunk.label}")
        self.chunk.buildPointCloud()

    def build_model(self):
        print(f"\n----\nBuilding model for chunk: {self.chunk.label}")
        self.chunk.buildModel(source_data = Metashape.DepthMapsData)

    def smooth_model(self):
        print(f"\n----\nSmoothing model for chunk: {self.chunk.label}")
        self.chunk.smoothModel(strength=6)

    def build_orthomosaic(self):
        print(f"\n----\nBuilding orthomosaic for chunk: {self.chunk.label}")
        self.chunk.buildOrthomosaic(surface_data=Metashape.DataSource.ModelData)
   
    def export_raster(self, export_folder):
        # for now, the export must be done locally and moved to the NAS as of some
        # unresolved OSError issues...
        ortho_path_tmp = f"/tmp/tmp_orthos/{self.chunk.label}_orthomosaic.tif"

        # export results
        # correct path on NAS
        ortho_path = os.path.join(export_folder, f"{self.chunk.label}_orthomosaic.tif")
        self.chunk.exportReport(export_folder + '/report.pdf')

        # if chunk.model:
        #     chunk.exportModel(output_folder + '/model.obj')

        # if chunk.point_cloud:
        #     chunk.exportPointCloud(output_folder + '/point_cloud.las', source_data = Metashape.PointCloudData)

        # if chunk.elevation:
        #     chunk.exportRaster(output_folder + '/dem.tif', source_data = Metashape.ElevationData)

        if self.chunk.orthomosaic:
            compression = Metashape.ImageCompression()
            compression.tiff_compression = Metashape.ImageCompression.TiffCompressionJPEG
            compression.jpeg_quality = 90
            compression.tiff_big = True
            compression.tiff_overviews = True
            compression.tiff_tiled = True
            
            out_projection = Metashape.OrthoProjection()
            out_projection.type = Metashape.OrthoProjection.Type.Planar
            out_projection.crs = Metashape.CoordinateSystem("EPSG::4326")

            # hier muss man noch etwas anpassen, da es beim schreiben zu einem OSError kommt:
            # doc.chunk.exportRaster("/mnt/gsdata/projects/other/agisoft_script_test/testflight_1_unprocessed/testortho.tiff", source_data=Metashape.OrthomosaicData, image_compression=Metashape.ImageCompression())
            # ExportRaster: path = /mnt/gsdata/projects/other/agisoft_script_test/testflight_1_unprocessed/testortho.tiff
            # generating 33892 x 12515 raster in 1 x 1 tiles
            # libtiff error: Write error at scanline 8384
            # libtiff error: Error writing TIFF header
            # Traceback (most recent call last):
            # File "<stdin>", line 1, in <module>
            # OSError: Can't write file: Permission denied (13): /mnt/gsdata/projects/other/agisoft_script_test/testflight_1_unprocessed/testortho.tiff
            self.chunk.exportRaster(path = ortho_path_tmp, 
                                    source_data = Metashape.OrthomosaicData,
                                    image_compression = compression,
                                    save_alpha = False,
                                    white_background = True,
                                    projection = out_projection)
            print(f"\n----\nExported orthomosaic to {ortho_path_tmp}")
            print(f"\n**Now moving exported orthomosaic to NAS destination: {ortho_path}")
            move_file(ortho_path_tmp, ortho_path)

    # def export_orthomosaic(self, export_folder):
    #     orthomosaic_path = os.path.join(export_folder, f"{self.chunk.label}.tif")
    #     self.chunk.exportRaster(orthomosaic_path, image_format=Metashape.ImageFormatTIFF)
    #     print(f"\n----\nExported orthomosaic to {orthomosaic_path}")

class MetashapeProcessor:
    def __init__(self, input_folder, use_both_gpu=False, use_gpu_index=0):
        self.input_folder = input_folder
        if use_both_gpu:
            print("***using both GPUs***")
            # Enable both GPUs
            Metashape.app.gpu_mask = (1 << 0) | (1 << 1)  # This enables GPU 0 and GPU 1
        else:
            print(f"***using GPU with index #{use_gpu_index}***")
            # Set the GPU mask based on the passed GPU index
            Metashape.app.gpu_mask = 1 << use_gpu_index  # Shift bit to select GPU
        Metashape.app.cpu_enable = False  # Optionally disable CPU processing
    
    def process_folders(self):
        for folder_name in sorted(os.listdir(self.input_folder)):
            print("Looping through all <..._unprocessed> folders")
            folder_path = os.path.join(self.input_folder, folder_name)
            if os.path.isdir(folder_path) and "_unprocessed" in folder_name:
                self.process_unprocessed_folder(folder_path)

    def process_unprocessed_folder(self, folder_path):
        print(f"Processing folder: {folder_path}")
        
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
                    
                    print("\n\n----Adding photos to individual chunk----\n\n")
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

                    # export all desired files
                    print_timestamp()
                    processor.export_raster(export_folder)
                    project.save()
                    
        # Save the project file
        project.save()
        # close the project file
        project.close()
        
        # Rename the processed folder from _unprocessed to _processed
        processed_folder = folder_path.replace("_unprocessed", "_processed")
        os.rename(folder_path, processed_folder)
        print(f"Renamed folder to: {processed_folder}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python3 pipeline.py <input_folder> <use_both_gpu> <use_gpu_index>")
        sys.exit(1)

    input_folder = sys.argv[1]
    use_both_gpu = sys.argv[2]
    use_gpu_index = sys.argv[3]

    # Initialize the previous timestamp as None
    previous_timestamp = None

    def print_timestamp():
        global previous_timestamp
        # Get the current time
        now = datetime.now()
        
        # Format the current timestamp
        formatted_timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        
        # Calculate the elapsed time
        if previous_timestamp is not None:
            elapsed_time = now - previous_timestamp
            formatted_elapsed_time = str(elapsed_time)
        else:
            formatted_elapsed_time = "N/A"
        
        # Print the current timestamp and elapsed time
        print(f"Current Timestamp: {formatted_timestamp}")
        print(f"Time elapsed since last timestamp: {formatted_elapsed_time}")
        
        # Update the previous timestamp
        previous_timestamp = now

    processor = MetashapeProcessor(input_folder, use_both_gpu, use_gpu_index)
    processor.process_folders()