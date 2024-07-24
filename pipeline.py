import os
import sys
from datetime import datetime
# Metashape should be installed in your local environment (best with python 3.9)
# follow: https://agisoft.freshdesk.com/support/solutions/articles/31000148930-how-to-install-metashape-stand-alone-python-module
import Metashape

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

class MetashapeProject:
    def __init__(self, project_path):
        self.doc = Metashape.Document()
        self.project_path = project_path
    
    def save(self):
        self.doc.save(self.project_path)

    def add_chunk(self, chunk_name, image_list):
        chunk = self.doc.addChunk()
        chunk.label = chunk_name
        chunk.addPhotos(image_list)
        print(str(len(chunk.cameras)) + " images loaded")
        return chunk

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
        # export results
        ortho_path = os.path.join(export_folder, f"{self.chunk.label}_orthomosaic.tif")
        self.chunk.exportReport(export_folder + '/report.pdf')

        # if chunk.model:
        #     chunk.exportModel(output_folder + '/model.obj')

        # if chunk.point_cloud:
        #     chunk.exportPointCloud(output_folder + '/point_cloud.las', source_data = Metashape.PointCloudData)

        # if chunk.elevation:
        #     chunk.exportRaster(output_folder + '/dem.tif', source_data = Metashape.ElevationData)

        if self.chunk.orthomosaic:
            self.chunk.exportRaster(ortho_path, source_data = Metashape.OrthomosaicData)
            print(f"\n----\nExported orthomosaic to {ortho_path}")

    # def export_orthomosaic(self, export_folder):
    #     orthomosaic_path = os.path.join(export_folder, f"{self.chunk.label}.tif")
    #     self.chunk.exportRaster(orthomosaic_path, image_format=Metashape.ImageFormatTIFF)
    #     print(f"\n----\nExported orthomosaic to {orthomosaic_path}")

class MetashapeProcessor:
    def __init__(self, input_folder):
        self.input_folder = input_folder
    
    def process_folders(self):
        for folder_name in sorted(os.listdir(self.input_folder)):
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
        project = Metashape.Document()
        project.save(project_path)

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
        
        # Rename the processed folder from _unprocessed to _processed
        processed_folder = folder_path.replace("_unprocessed", "_processed")
        os.rename(folder_path, processed_folder)
        print(f"Renamed folder to: {processed_folder}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 pipeline.py <input_folder>")
        sys.exit(1)

    input_folder = sys.argv[1]

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

    processor = MetashapeProcessor(input_folder)
    processor.process_folders()