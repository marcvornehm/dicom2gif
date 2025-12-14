from collections import defaultdict
from pathlib import Path

import pydicom
import pydicom.uid

from .cine import Cine, CineEnhanced, CineLegacy


def read_dcm(dcm_file: str | Path) -> Cine:
    """Read a DICOM file and return a Cine object.

    Args:
        dcm_file (str | Path): Path to the DICOM file.

    Returns:
        Cine: Cine object representing the cine series in the DICOM file. If the
            DICOM file is a legacy (non-enhanced) DICOM, the Cine object also
            includes all other files in the same series found in the directory.

    Raises:
        ValueError: If the DICOM file does not exist or has an unsupported SOP
            Class UID
    """
    dcm_file = Path(dcm_file)
    if not dcm_file.exists():
        raise ValueError(f"{dcm_file} does not exist.")
    dcm_dset = pydicom.dcmread(dcm_file)
    sop_uid = dcm_dset.SOPClassUID
    if sop_uid == pydicom.uid.MRImageStorage:
        # find all files of the same series
        dcm_dir = dcm_file.parent
        dcm_dsets = [pydicom.dcmread(f) for f in sorted(dcm_dir.rglob("*.dcm"))]
        dcm_dsets = filter(
            lambda d: d.SeriesInstanceUID == dcm_dset.SeriesInstanceUID, dcm_dsets
        )
        cine = CineLegacy(dcm=dcm_dsets)
    elif sop_uid == pydicom.uid.EnhancedMRImageStorage:
        cine = CineEnhanced(dcm=dcm_dset)
    else:
        raise ValueError(f"Unsupported SOP Class UID: {sop_uid}")

    return cine


def read_dir(dcm_dir: str | Path, pattern: str = "*.dcm") -> dict[Path, Cine]:
    """Read DICOM files from a directory and group them by SeriesInstanceUID.

    Args:
        dcm_dir (str | Path): Directory containing DICOM files.
        pattern (str): Glob pattern to match DICOM files. Defaults to '*.dcm'.

    Returns:
        dict[Path, Cine]: Dictionary mapping the path of a representative DICOM
            file to a Cine object containing the DICOM datasets.

    Raises:
        ValueError: If the directory does not exist or is not a directory.
    """
    dcm_dir = Path(dcm_dir)
    if not dcm_dir.exists():
        raise ValueError(f"{dcm_dir} does not exist.")
    if not dcm_dir.is_dir():
        raise ValueError(f"{dcm_dir} is not a directory.")

    dcm_files = list(sorted(dcm_dir.rglob(pattern)))
    series_enhanced = []
    series_legacy = defaultdict(list)

    for dcm_file in dcm_files:
        dcm_dset = pydicom.dcmread(dcm_file)
        sop_uid = dcm_dset.SOPClassUID
        if sop_uid == pydicom.uid.MRImageStorage:
            series_legacy[dcm_dset.SeriesInstanceUID].append((dcm_file, dcm_dset))
        elif sop_uid == pydicom.uid.EnhancedMRImageStorage:
            series_enhanced.append((dcm_file, dcm_dset))

    cines = {}
    for dcm_file, dcm_dset in series_enhanced:
        cine = CineEnhanced(dcm=dcm_dset)
        cines[dcm_file] = cine
    for dcm_list in series_legacy.values():
        paths, dsets = zip(*dcm_list)
        cine = CineLegacy(dcm=dsets)
        cines[sorted(paths)[0]] = cine

    return cines
