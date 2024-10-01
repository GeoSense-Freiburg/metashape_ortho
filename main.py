import sys
import os
from pipeline.metashape_processor import MetashapeProcessor
from pipeline.utils import create_log_file, check_free_space, load_config

def display_summary(input_folder, gpu_option, cpu_enabled, log_file):
    """
    Displays a summary of the current configuration and lists unprocessed folders and chunks.

    Args:
        input_folder (str): The folder containing the input data.
        gpu_option (str): The GPU option used for processing.
        cpu_enabled (bool): Whether CPU processing is enabled.
        log_file (str): The path to the log file.
    """
    print("\n--- Summary of Execution ---")
    print(f"Input Folder: {input_folder}")
    print(f"GPU Option: {gpu_option}")
    print(f"CPU Enabled: {cpu_enabled}")
    print(f"Log directory: {log_file}")

    print("\nUnprocessed Folders and Chunks:")
    for folder_name in sorted(os.listdir(input_folder)):
        folder_path = os.path.join(input_folder, folder_name)
        if os.path.isdir(folder_path) and "_unprocessed" in folder_name:
            print(f"  - {folder_path}")
            photos_dir = os.path.join(folder_path, "photos")
            if os.path.isdir(photos_dir):
                for subfolder_name in sorted(os.listdir(photos_dir)):
                    subfolder_path = os.path.join(photos_dir, subfolder_name)
                    if os.path.isdir(subfolder_path):
                        print(f"    - Chunk: {subfolder_name}")
    
    # Check free disk space before proceeding
    try:
        check_free_space(100, "/mnt/data/")
        print("\nDo you want to proceed with these settings? (yes/no)")
    except RuntimeError as e:
        print(f"Error during free space check: {e}")
        sys.exit(1)

def main():
    """
    Main function that orchestrates the processing of input folders using Metashape.
    
    Steps:
    1. Load configuration file.
    2. Display summary of settings.
    3. Confirm with the user to proceed.
    4. Initialize and process folders using MetashapeProcessor.
    """
    if len(sys.argv) != 2:
        print("Usage: python3 main.py <config_file>")
        sys.exit(1)

    try:
        # Load configuration from the specified YAML file
        config = load_config(sys.argv[1])
        input_folder = config["input_folder"]
        gpu_option = config["gpu_option"]
        cpu_enabled = config["cpu_enabled"]
        log_dir = config["log_dir"]
    except FileNotFoundError:
        print(f"Config file {sys.argv[1]} not found.")
        sys.exit(1)
    except KeyError as e:
        print(f"Missing required config key: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error loading config: {e}")
        sys.exit(1)

    # Automatically create the log file in the "log-files" folder
    try:
        log_file = create_log_file(log_dir)
    except Exception as e:
        print(f"Failed to create log file: {e}")
        sys.exit(1)

    # Display summary and ask for confirmation
    display_summary(input_folder, gpu_option, cpu_enabled, log_file)

    user_input = input("Type 'yes' to proceed or 'no' to abort: ").strip().lower()
    if user_input != 'yes':
        print("Aborting the script.")
        sys.exit(0)

    # Initialize MetashapeProcessor and process the folders
    try:
        processor = MetashapeProcessor(config, log_file)
        processor.process_folders()
    except Exception as e:
        print(f"Error during processing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
