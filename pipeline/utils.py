import os
import sys
import shutil
import logging
import yaml
from datetime import datetime

class StreamToLogger:
    """
    Redirects stdout and stderr to the logger.

    Args:
        logger (logging.Logger): The logger instance to use.
        log_level (int): The logging level for the output stream.
    """
    def __init__(self, logger, log_level):
        self.logger = logger
        self.log_level = log_level
        self.linebuf = ''

    def write(self, buf):
        """
        Writes output to the logger, line by line.
        """
        for line in buf.rstrip().splitlines():
            self.logger.log(self.log_level, line.rstrip())

    def flush(self):
        """
        Flush method, required by the IO base class.
        """
        pass

def setup_logger(log_file):
    """
    Sets up the logging configuration, redirecting stdout and stderr 
    to the logger. Logs to both console and file.

    Args:
        log_file (str): Path of the log file.

    Returns:
        logging.Logger: Configured logger.
    """
    print("Setting up logger")
    logger = logging.getLogger()

    # Avoid adding handlers multiple times
    logger.setLevel(logging.DEBUG)

    # Create handlers for file and console
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Define log format
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # Set formatter for handlers
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Redirect stdout and stderr
    sys.stdout = StreamToLogger(logger, logging.INFO)
    sys.stderr = StreamToLogger(logger, logging.ERROR)

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
    os.makedirs(log_folder, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file_name = f"log_{timestamp}.log"
    log_file_path = os.path.join(log_folder, log_file_name)

    return log_file_path

def move_file(source_path, destination_path):
    """
    Moves a file from source to destination path.

    Args:
        source_path (str): Source file path.
        destination_path (str): Destination file path.
    """
    try:
        shutil.move(source_path, destination_path)
        logging.info(f"File moved successfully from {source_path} to {destination_path}")
    except FileNotFoundError:
        logging.error(f"File not found: {source_path}")
    except PermissionError:
        logging.error(f"Permission denied when moving file: {source_path}")
    except Exception as e:
        logging.error(f"Unexpected error moving file from {source_path} to {destination_path}: {e}")

def move_all_files(src_dir, dest_dir):
    """
    Moves all files and subfolders from source directory to destination directory.

    Args:
        src_dir (str): Source directory.
        dest_dir (str): Destination directory.

    Raises:
        FileNotFoundError: If the source directory doesn't exist.
        Exception: If any error occurs during file moving.
    """
    if not os.path.exists(src_dir):
        raise FileNotFoundError(f"Source directory {src_dir} does not exist.")
    
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
        logging.info(f"Created destination directory: {dest_dir}")
    
    for item in os.listdir(src_dir):
        src_path = os.path.join(src_dir, item)
        dest_path = os.path.join(dest_dir, item)

        try:
            if os.path.isdir(src_path):
                shutil.move(src_path, dest_path)
                logging.info(f"Moved directory: {src_path} to {dest_path}")
            else:
                shutil.move(src_path, dest_path)
                logging.info(f"Moved file: {src_path} to {dest_path}")
        except FileNotFoundError:
            logging.error(f"File or directory not found: {src_path}")
        except PermissionError:
            logging.error(f"Permission denied when moving: {src_path}")
        except Exception as e:
            logging.error(f"Unexpected error moving {src_path} to {dest_path}: {e}")
            raise

    logging.info(f"All files and subfolders moved from {src_dir} to {dest_dir}")

def check_free_space(min_required_space_gb, folder):
    """
    Checks if the disk has enough free space.

    Args:
        min_required_space_gb (float): Minimum required space in GB.
        folder (str): Folder path to check the disk usage.

    Raises:
        RuntimeError: If there is not enough free disk space.
    """
    total, used, free = shutil.disk_usage(folder)
    free_gb = free / (1024 ** 3)  # Convert to GB
    if free_gb < min_required_space_gb:
        logging.error(f"Not enough disk space. Required: {min_required_space_gb} GB, Available: {free_gb:.2f} GB.")
        raise RuntimeError(f"Not enough disk space. Required: {min_required_space_gb} GB, Available: {free_gb:.2f} GB.")
    
    logging.info(f"Disk space check passed: {free_gb:.2f} GB available.")

def load_config(config_file='config.yaml'):
    """
    Loads configuration from a YAML file.

    Args:
        config_file (str): Path to the configuration file.

    Returns:
        dict: Configuration data from the YAML file.

    Raises:
        FileNotFoundError: If the config file is not found.
    """
    if not os.path.exists(config_file):
        logging.error(f"Config file not found: {config_file}")
        raise FileNotFoundError(f"Config file {config_file} does not exist.")
    
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
    
    logging.info(f"Configuration loaded from {config_file}")
    return config

def remove_lockfile(project_path):
    """
    Removes a lockfile associated with the project if it exists.

    Args:
        project_path (str): Path to the project file.

    Logs:
        Success or failure of the lockfile removal.
    """
    lockfile = project_path.replace(".psx", ".files/lock")

    try:
        os.remove(lockfile)
        logging.info(f"Lockfile deleted: {lockfile}")
    except FileNotFoundError:
        logging.warning(f"No lockfile found: {lockfile}")
    except PermissionError:
        logging.error(f"Permission denied when deleting lockfile: {lockfile}")
    except Exception as e:
        logging.error(f"Unexpected error when deleting lockfile: {e}")
