# Metashape processor
This project provides a script for automating the processing of orthoimagery using Agisoft Metashape. It handles the alignment of photos, depth map generation, point cloud creation, model building, and orthomosaic export. The script also supports GPU processing for performance optimization.

## Features (implemented so far)

- **Photo Alignment:** Aligns photos for each chunk in a Metashape project.
- **Depth Map Generation:** Builds depth maps from aligned photos.
- **Point Cloud Generation:** Creates a point cloud from depth maps.
- **Model Building:** Builds a 3D model from the point cloud.
- **Model Smoothing:** Smooths the 3D model.
- **Orthomosaic Creation:** Generates an orthomosaic from the 3D model.
- **GPU Support:** Optionally use one or both GPUs for processing.
- **Logging:** Logs detailed processing information to files.

## Requirements

- Python 3.9+
- Conda (for environment management)
- Agisoft Metashape (Python module)
- shutil, os, sys, datetime, logging (standard Python libraries)

## Installation

### 1. clone the repository

```
git clone <repository-url>
cd agisoft_ortho
```

### 2. create and activate a conda environment

```
conda env create -f environment.yml
conda activate <your-environment-name>
```

### 3. install required/missing packages

Ensure Metashape is installed in your environment. If not, follow the [Metashape installation guide](https://agisoft.freshdesk.com/support/solutions/articles/31000148930-how-to-install-metashape-stand-alone-python-module).

## Usage

### If working on PYLOS

If working on PYLOS, the use of `tmux` or similar is recommended to keep the process going even if you logout or use the terminal in any other way.

### 1. Prepare your data

The folder structure of your data/flights should be like this:
```
<input_folder>/
├── <some_unprocessed_folder>_unprocessed/
│   ├── photos/
│   │   ├── <chunk1>/
│   │   └── <chunk2>/
...and so on
```

### 2. Run the script

```
python3 main.py <input_folder> <gpu_option> <cpu_enabled>
```

#### To use GPU 0
`python3 main.py <input_folder> 0 0`

#### To use GPU 1
`python3 main.py <input_folder> 1 0`

#### To use both GPUs
`python3 main.py <input_folder> both 0`

### 3. confirm the execution on your parameters

The script will display a summary of actions and ask for confirmation before proceeding.

## package structure

```
agisoft_ortho/
│
├── pipeline/
│   ├── __init__.py
│   ├── metashape_processor.py  # The core functions and classes
│   ├── utils.py                # Helper functions are stored inside here
├── setup.py
├── README.md
├── main.py             # the main pipeline call
└── environment.yml     # conda environment
```



## Log Files

Log files are being created with each execution of the pipeline. The logfiles are stored within `<input_folder>/log-files`

```
log-files/
│
├── 2024-09-10_15-30-00.log
├── 2024-09-10_15-45-00.log
└── ...
```

## Development

To contribute or modify the code:

1. Fork the Repository
2. Create a Branch
3. Make Changes and Test
4. Submit a Pull Request

## License

This project is licensed under the MIT License.

## Acknowledgements

Agisoft Metashape for photogrammetry tools.
Python and Conda for managing dependencies and environments.