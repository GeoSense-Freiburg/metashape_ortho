import sys
import os
from pipeline.metashape_processor import MetashapeProcessor
from pipeline.utils import create_log_file, print_timestamp

def display_summary(input_folder, gpu_option, cpu_enabled):
    print("\n--- Summary of Execution ---")
    print(f"Input Folder: {input_folder}")
    print(f"GPU Option: {gpu_option}")
    print(f"CPU Enabled: {cpu_enabled}")

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
    
    print("\nDo you want to proceed with these settings? (yes/no)")

def main():
    if len(sys.argv) != 4:
        print("Usage: python3 main.py <input_folder> <gpu_option> <cpu_enabled>")
        print("<gpu_option> should be '0', '1', or 'both'")
        print("<cpu_option> should be '0' or '1'")
        sys.exit(1)

    input_folder = sys.argv[1]
    gpu_option = sys.argv[2]  # '0', '1', or 'both'
    cpu_enabled = bool(int(sys.argv[3]))

    # Automatically create the log file with a timestamp in the "log-files" folder
    log_file = create_log_file(input_folder)

    # Display summary and ask for confirmation
    display_summary(input_folder, gpu_option, cpu_enabled)

    user_input = input("Type 'yes' to proceed or 'no' to abort: ").strip().lower()
    if user_input != 'yes':
        print("Aborting the script.")
        sys.exit(0)

    # Initialize and start the processing
    processor = MetashapeProcessor(input_folder, log_file, gpu_option, cpu_enabled)
    processor.process_folders()

if __name__ == "__main__":
    main()
