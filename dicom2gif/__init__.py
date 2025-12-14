"""dicom2gif - Convert DICOM cine series to GIF format (and others)."""

from .cine import Cine, CineEnhanced, CineLegacy
from .dicom2gif import dicom2gif
from .read import read_dcm, read_dir
from .write import write_gif

__version__ = "0.1.0"
__all__ = [
    "Cine",
    "CineEnhanced",
    "CineLegacy",
    "dicom2gif",
    "read_dcm",
    "read_dir",
    "write_gif",
]
