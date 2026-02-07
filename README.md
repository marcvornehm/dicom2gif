# dicom2gif

A Python tool to convert DICOM series to GIF/APNG/TIFF format

## Features

- Convert enhanced (multi-frame) and legacy DICOM series to GIF, APNG, or TIFF
- Automatic detection of frame duration from DICOM metadata
- Support for windowing (brightness/contrast) adjustment
- Batch processing of entire directories
- Select range of frames to save

## Installation

```bash
pip install dicom2gif
```

## Usage

### Command Line

After installation, `dicom2gif` can be used as a command line tool.
When given a directory, the tool will recursively search for DICOM files with the same Series Instance UID and create a separate movie file for each series.

```bash
dicom2gif [-h] [-p PATTERN] [-o OUT_FILE] [-f {gif,apng,tiff}] [-d DURATION] [-w WINDOWING] [--frames FRAMES] dcm_path
```

Options:

- `dcm_path`: Input DICOM file or directory
- `-p, --pattern`: Pattern to select DICOM files when `dcm_path` is a directory (defaults to *.dcm)
- `-o, --out_file`: Output file path (defaults to input name with .gif extension)
- `-f, --format`: Output file format, can be gif, apng, or tiff (ignored if `--out_file` is given)
- `-d, --duration`: Duration per frame in milliseconds (optional, auto-detected from DICOM if available)
- `-w, --windowing`: Can be two comma-separated integers for window center and width, 'dicom' for windowing parameters from DICOM metadata, or 'full' for windowing to full dynamic range (defaults to 'dicom')
- `--frames`: Frame range (1-based, inclusive). Examples: '5' (frame 5 only), '10-20' (frames 10 to 20), '10-' (frame 10 to end), '-20' (start to frame 20).

### Python API

```python
from dicom2gif import dicom2gif, read_dcm, read_dir, write

# Single enhanced DICOM file
series = read_dcm("path/to/file.dcm")
write(series, "output.gif", duration=50)

# Directory of DICOM files
all_series = read_dir("path/to/directory")
for path, series in all_series.items():
    out_file = path.with_suffix(".apng")
    write(series, out_file, windowing="dicom")

# Or directly
dicom2gif("path/to/file.dcm", out_file="output.gif", duration=50)
dicom2gif("path/to/directory", format="apng", windowing="full", frame_start=2, frame_end=10)
```

## Requirements

- Python ≥ 3.10
- numpy
- Pillow ≥ 7.1.2
- pydicom
