import pytest
from pipeline.utils import load_config, check_free_space

def test_load_config_valid():
    config = load_config("tests/test_config.yaml")
    assert config["input_folder"] == "test_input"
    assert config["gpu_option"] == "gpu"

def test_load_config_file_not_found():
    with pytest.raises(FileNotFoundError):
        load_config("non_existent_file.yaml")

def test_check_free_space_enough_space(monkeypatch):
    def mock_disk_usage(path):
        return (1000, 500, 600 * 1024**3)  # Mock values in GB
    monkeypatch.setattr("shutil.disk_usage", mock_disk_usage)
    check_free_space(100, "/mnt/data/")

def test_check_free_space_not_enough_space(monkeypatch):
    def mock_disk_usage(path):
        return (1000, 500, 50 * 1024**3)  # Mock values in GB
    monkeypatch.setattr("shutil.disk_usage", mock_disk_usage)
    with pytest.raises(RuntimeError):
        check_free_space(100, "/mnt/data/")
