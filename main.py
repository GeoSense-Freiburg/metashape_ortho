import sys
import os
from pipeline.metashape_processor import MetashapeProcessor
from pipeline.utils import create_log_file, check_free_space, load_config

def display_summary(input_folder, gpu_option, cpu_enabled, log_file):
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
    
    check_free_space(100, "/mnt/data/")
    print("\nDo you want to proceed with these settings? (yes/no)")

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 main.py <config_file>")
        sys.exit(1)

    config = load_config(sys.argv[1])
    print(config)
    input_folder = config["input_folder"]
    gpu_option = config["gpu_option"]
    cpu_enabled = config["cpu_enabled"]
    log_dir = config["log_dir"]

    # Automatically create the log file with a timestamp in the "log-files" folder
    log_file = create_log_file(log_dir)

    # Display summary and ask for confirmation
    display_summary(input_folder, gpu_option, cpu_enabled, log_file)

    user_input = input("Type 'yes' to proceed or 'no' to abort: ").strip().lower()
    if user_input != 'yes':
        print("Aborting the script.")
        sys.exit(0)

    # Initialize and start the processing
    processor = MetashapeProcessor(config, log_file)
    processor.process_folders()

if __name__ == "__main__":
    main()
