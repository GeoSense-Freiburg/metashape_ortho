import os
import sys
# Metashape should be installed in your local environment (best with python 3.9)
# follow: https://agisoft.freshdesk.com/support/solutions/articles/31000148930-how-to-install-metashape-stand-alone-python-module
import Metashape

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
        return chunk

class MetashapeChunkProcessor:
    def __init__(self, chunk):
        self.chunk = chunk

    def align_photos(self):
        print(f"Aligning photos for chunk: {self.chunk.label}")
        self.chunk.matchPhotos(accuracy=Metashape.HighAccuracy, preselection=Metashape.ReferencePreselection)
        self.chunk.alignCameras()

    def build_point_cloud(self):
        print(f"Building point cloud for chunk: {self.chunk.label}")
        self.chunk.buildDenseCloud(quality=Metashape.MediumQuality, filter=Metashape.AggressiveFiltering)

    def build_model(self):
        print(f"Building model for chunk: {self.chunk.label}")
        self.chunk.buildModel(surface=Metashape.HeightField, interpolation=Metashape.EnabledInterpolation)

    def smooth_model(self):
        print(f"Smoothing model for chunk: {self.chunk.label}")
        self.chunk.smoothModel(strength=6)

    def build_orthomosaic(self):
        print(f"Building orthomosaic for chunk: {self.chunk.label}")
        self.chunk.buildOrthomosaic(surface_data=Metashape.DataSource.ModelData, blending=Metashape.MosaicBlending)

    def export_orthomosaic(self, export_folder):
        orthomosaic_path = os.path.join(export_folder, f"{self.chunk.label}.tif")
        self.chunk.exportOrthomosaic(orthomosaic_path, image_format=Metashape.ImageFormatTIFF)
        print(f"Exported orthomosaic to {orthomosaic_path}")

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
        project = MetashapeProject(project_path)

        # Locate the "photos" directory within the "_unprocessed" folder
        photos_dir = os.path.join(folder_path, "photos")
        if os.path.isdir(photos_dir):
            for subfolder_name in sorted(os.listdir(photos_dir)):
                subfolder_path = os.path.join(photos_dir, subfolder_name)
                if os.path.isdir(subfolder_path):
                    image_list = [os.path.join(subfolder_path, file_name) for file_name in os.listdir(subfolder_path) if file_name.endswith(".jpg")]
                    if not image_list:
                        continue
                    
                    chunk = project.add_chunk(subfolder_name, image_list)
                    processor = MetashapeChunkProcessor(chunk)
                    processor.align_photos()
                    processor.build_point_cloud()
                    processor.build_model()
                    processor.smooth_model()
                    processor.build_orthomosaic()
                    processor.export_orthomosaic(export_folder)

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

    processor = MetashapeProcessor(input_folder)
    processor.process_folders()

    print("script loaded successfull")
