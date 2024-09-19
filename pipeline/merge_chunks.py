import os
import Metashape
import time
import logging
from pipeline.utils import setup_logger, move_file, move_all_files, remove_lockfile
from pipeline.metashape_processor import MetashapeChunkProcessor
from datetime import datetime
from pathlib import Path

os.environ["CUDA_VISIBLE_DEVICES"]="0"

'''
Merge chunks in biologie-konrad project that already exists (helper script for now)
this needs to be implemented to the whole script at some point to match for all!

needs to iterate through the relevant chunks (RGB, R, IR, ....)
'''

class MetashapeProject:
    def __init__(self, project_path):
        self.doc = Metashape.Document()
        self.project_path = project_path

    def save(self):
        remove_lockfile(self.project_path)
        self.doc.save(self.project_path)
        time.sleep(5)
        remove_lockfile(self.project_path)

# copy project to tmp folder
project_path = "/mnt/gsdata/projects/other/Biologie_Konrad/multispektral_processed/project.psx"
tmp_project_path = '/mnt/data/tmp_orthos/biologie/project.psx'

# move project.psx and project.files
move_file(project_path, tmp_project_path)

project_files_path = project_path.replace(".psx", ".files")
tmp_project_files_path = tmp_project_path.replace(".psx", ".files")

move_all_files(project_files_path, tmp_project_files_path)

# Define the path for the project file
project = MetashapeProject(tmp_project_path)

# Merging chunks
merged_chunk = project.mergeChunks(chunks=project.chunks, merge_dense_clouds=True, merge_models=True, merge_markers=True)

processor = MetashapeChunkProcessor(merged_chunk)

#
processor.build_depth_maps()
project.save()

#
processor.build_model()
project.save()

has_transform = chunk.transform.scale and chunk.transform.rotation and chunk.transform.translation

if has_transform:
    #
    processor.build_point_cloud()
    project.save()

    #
    processor.smooth_model()
    project.save()

    #
    processor.build_orthomosaic()
    project.save()

# Export orthomosaic for each channel (RGB, NIR, RE, R, G)
#
export_folder = os.path.dirname(tmp_project_path)
processor.export_raster(export_folder)
project.save()

print("Orthomosaic created successfully!")