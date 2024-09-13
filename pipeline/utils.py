import os
import sys
import shutil
import logging
import yaml
from datetime import datetime

# Set up a logger that outputs both to the console and to a file
def setup_logger(log_file):
    logger = logging.getLogger()  # Root logger

    # Check if the logger already has handlers to avoid duplicate logs
    if not logger.hasHandlers():
        logger.setLevel(logging.DEBUG)

        # Create a file handler for logging to a file
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)

        # Create a console handler for logging to the console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Define the log format
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

        # Add formatter to both handlers
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # Add the handlers to the logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger

def create_log_file(input_folder):
    """
    Creates a log file in the 'log-files' directory inside the input folder.
    Args:
        input_folder (str): Path to the input folder.
    
    Returns:
        str: Full path to the log file.
    """
    log_folder = os.path.join(input_folder, "log-files")
    os.makedirs(log_folder, exist_ok=True)  # Create log folder if it doesn't exist

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file_name = f"log_{timestamp}.log"
    log_file_path = os.path.join(log_folder, log_file_name)

    return log_file_path

def move_file(source_path, destination_path):
    """
    Moves file from source to destination path.
    Args:
        source_path (str): Source file path.
        destination_path (str): Destination file path.
    """
    try:
        shutil.move(source_path, destination_path)
        logging.info(f"File moved successfully from {source_path} to {destination_path}")
    except Exception as e:
        logging.error(f"Error moving file: {e}")

def move_all_files(src_dir, dest_dir):
    """
    Move all files and subfolders from source directory to destination directory.
    
    Args:
        src_dir (str): The source directory from where files and subfolders will be moved.
        dest_dir (str): The destination directory where files and subfolders will be moved to.
        
    Raises:
        FileNotFoundError: If the source directory doesn't exist.
        Exception: If an error occurs during the file moving process.
    """
    if not os.path.exists(src_dir):
        raise FileNotFoundError(f"Source directory {src_dir} does not exist.")
    
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
        logging.info(f"Created destination directory: {dest_dir}")
    
    # Iterate over all items in the source directory
    for item in os.listdir(src_dir):
        src_path = os.path.join(src_dir, item)
        dest_path = os.path.join(dest_dir, item)

        try:
            if os.path.isdir(src_path):
                # If it's a directory, move the entire directory
                shutil.move(src_path, dest_path)
                logging.info(f"Moved directory: {src_path} to {dest_path}")
            else:
                # If it's a file, move the file
                shutil.move(src_path, dest_path)
                logging.info(f"Moved file: {src_path} to {dest_path}")
        except Exception as e:
            logging.error(f"Error moving {src_path} to {dest_path}: {e}")
            raise

    logging.info(f"All files and subfolders moved from {src_dir} to {dest_dir}")
    
# def print_timestamp(previous_timestamp=None):
#     """
#     Logs the current timestamp and time elapsed since the previous timestamp.
#     Args:
#         previous_timestamp (datetime, optional): Previous timestamp. Defaults to None.
    
#     Returns:
#         datetime: Current timestamp.
#     """
#     now = datetime.now()
#     formatted_timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    
#     if previous_timestamp:
#         elapsed_time = now - previous_timestamp
#         formatted_elapsed_time = str(elapsed_time)
#     else:
#         formatted_elapsed_time = "N/A"
    
#     logging.info(f"Current Timestamp: {formatted_timestamp}")
#     logging.info(f"Time elapsed: {formatted_elapsed_time}")
    
#     return now

def check_free_space(min_required_space_gb, folder):
    """Check if there is enough free space on the disk."""
    total, used, free = shutil.disk_usage(folder)
    free_gb = free / (1024 ** 3)  # Convert to GB
    if free_gb < min_required_space_gb:
        raise RuntimeError(f"Not enough disk space. Required: {min_required_space_gb} GB, Available: {free_gb:.2f} GB.")
    logging.info(f"Disk space check passed: {free_gb:.2f} GB available.")

def load_config(config_file='config.yaml'):
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"Config file {config_file} does not exist.")
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
    return config