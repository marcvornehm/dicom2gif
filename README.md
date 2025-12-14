# dicom2gif

A Python tool to convert DICOMs of MRI cine series to GIF/APNG/TIFF format.

## Features

- Convert enhanced DICOM files (multi-frame) to GIF, APNG, or TIFF
- Convert legacy DICOM series to GIF, APNG, or TIFF
- Automatic detection of frame duration from DICOM metadata
- Support for windowing (brightness/contrast) adjustment
- Batch processing of entire directories

## Installation

```bash
pip install dicom2gif
```

## Usage

### Command Line

After installation, you can use the tool in three ways:

```bash
# As an installed script
dicom2gif path/to/dicom/file.dcm

# Using python -m
python -m dicom2gif path/to/dicom/file.dcm

# With custom output and duration
dicom2gif input.dcm -o output.gif -d 100
```

### Command Line Options

- `dcm_path`: Input DICOM file or directory
- `-p, --pattern`: Pattern to select DICOM files when `dcm_path` is a directory (defaults to *.dcm)
- `-o, --out_file`: Output file path (defaults to input name with .gif extension)
- `-f, --format`: Output file format, can be gif, apng, or tiff/tif (ignored if `--out_file` is given)
- `-d, --duration`: Duration per frame in milliseconds (optional, auto-detected from DICOM if available)
- `-w, --windowing`: Can be two comma-separated integers for window center and width, 'auto' for automatic windowing to full dynamic range, or None to use windowing parameters from DICOM metadata (defaults to None)

### Process a Directory

When given a directory, the tool will recursively:
- Create a separate GIF for each enhanced DICOM file
- Create a separate GIF for each series of legacy DICOM files as determined by their Series Instance UID

```bash
dicom2gif path/to/dicom/directory
```

### Python API

```python
from dicom2gif import dicom2gif, read_dcm, read_dir, write_gif

# Single DICOM file
cine = read_dcm("path/to/file.dcm")
write_gif(cine, "output.gif", duration=50)

# Directory of DICOM files
cines = read_dir("path/to/directory")
for path, cine in cines:
    out_file = path.with_suffix(".apng")
    write_gif(cine, out_file, windowing="auto")

# Or directly
dicom2gif("path/to/file.dcm", out_file="output.gif", duration=50)
dicom2gif("path/to/directory", format="apng", windowing="auto")
```

## Requirements

- Python ≥ 3.10
- numpy
- Pillow ≥ 7.1.2
- pydicom
