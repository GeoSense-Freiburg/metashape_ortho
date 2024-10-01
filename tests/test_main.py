import os
import pytest
import shutil
from pipeline.metashape_processor import MetashapeProcessor
from pipeline.utils import load_config, create_log_file

def test_main_processing():
    # Load a sample test config file
    config = load_config("tests/test_config.yaml")
    
    # Define the test input and log directory paths
    input_folder = config["input_folder"]
    log_dir = config["log_dir"]

    # Create a log file
    log_file = create_log_file(log_dir)

    # Initialize the processor and run it on the test folder
    processor = MetashapeProcessor(config, log_file)
    
    # Assume processor.process_folders() processes files and outputs some results
    processor.process_folders()
    
    # # Check if expected output files are created
    # output_files = ["expected_output_file1", "expected_output_file2"]
    # for file in output_files:
    #     assert os.path.exists(os.path.join(input_folder, file)), f"Output file {file} not found"

    # # Optionally, cleanup test output after validation
    # shutil.rmtree(input_folder)
