import warnings
from collections import defaultdict
from pathlib import Path

import numpy as np
import pydicom
from PIL import Image

from .series import DicomSeries

SUPPORTED_FORMATS = [".gif", ".apng", ".tiff", ".tif"]


def read_dcm(dcm_path: str | Path) -> DicomSeries:
    """Read a DICOM series from a file.

    Args:
        dcm_path (str | Path): Path to a DICOM file.

    Returns:
        DicomSeries: A DicomSeries object containing the DICOM data.
    """
    dcm_path = Path(dcm_path)
    if not dcm_path.exists() or not dcm_path.is_file():
        raise ValueError(f"{dcm_path} must be a path to a regular file.")
    dcm_dset = pydicom.dcmread(dcm_path)
    series = DicomSeries(dcm_dset)
    return series


def read_dir(dcm_path: str | Path, pattern: str = "*.dcm") -> dict[Path, DicomSeries]:
    """Read DICOM series from a directory.

    Args:
        dcm_path (str | Path): Path to the directory containing DICOM files. The
            function reads all files matching `pattern` and groups them into
            series based on their SeriesInstanceUID.
        pattern (str): Glob pattern to match DICOM files. Defaults to '*.dcm'.

    Returns:
        dict[Path, DicomSeries]: A dictionary mapping the path of a
            representative DICOM file to a DicomSeries object containing the
            DICOM data for the corresponding series.
    """
    dcm_path = Path(dcm_path)
    if not dcm_path.exists() or not dcm_path.is_dir():
        raise ValueError(f"{dcm_path} must be a path to an existing directory.")

    series_by_uid = defaultdict(list)
    for dcm_file in sorted(dcm_path.rglob(pattern)):
        dcm_dset = pydicom.dcmread(dcm_file)
        sop_class = dcm_dset.SOPClassUID
        if "PresentationStateStorage" in sop_class.keyword:
            continue  # skip presentation states
        series_by_uid[dcm_dset.SeriesInstanceUID].append((dcm_file, dcm_dset))

    series_by_file = dict()
    for dcm_list in series_by_uid.values():
        paths, dcm_dsets = zip(*dcm_list)
        main_path = sorted(paths)[0]
        series = DicomSeries(dcm_dsets)
        series_by_file[main_path] = series

    return series_by_file


def write(
    series: DicomSeries,
    out_path: str | Path,
    duration: int | None = None,
    windowing: tuple[int, int] | str = "dicom",
) -> None:
    """Save a Dicom series as a GIF/APNG/TIFF file.

    Args:
        series (DicomSeries): DicomSeries object to write.
        out_path (str | Path): Output file path. The file extension determines
            the file format. Allowed extensions are .gif, .apng, and .tiff/.tif.
        duration (int | None): Duration of each frame in milliseconds. If None,
            determined from the DICOM data. Defaults to None.
        windowing (tuple[int, int] | str): Either tuple of ints for window
            center and width, 'full' for full dynamic range, or 'dicom'. If
            'dicom', uses window center and width from DICOM metadata. Defaults
            to 'dicom'.
    """
    # Validate arguments
    if duration is not None and duration <= 0:
        raise ValueError(
            f"Duration must be None or a positive integer but was {duration}"
        )
    if isinstance(windowing, str):
        windowing = windowing.lower()
    if not (
        windowing == "full"
        or windowing == "dicom"
        or (isinstance(windowing, tuple) and len(windowing) == 2)
    ):
        raise ValueError(
            f"Windowing must be 'dicom', 'full', or a tuple of (center, width) but was "
            f"{windowing}"
        )

    # Get image data
    imgs = series.pixel_array
    if len(imgs.shape) == 2:
        imgs = imgs[None, :, :]
        warnings.warn(
            "Pixel array has only two dimensions. Interpreting as a single frame.",
            UserWarning,
        )

    # Apply windowing
    if isinstance(windowing, tuple):  # provided as argument
        w_center, w_width = windowing
        imgs = _apply_windowing(imgs, w_center, w_width)
    elif windowing == "dicom":  # read from DICOM metadata
        windowing_dcm = series.get_windowing()
        if windowing_dcm is not None:
            w_center, w_width = windowing_dcm
            imgs = _apply_windowing(imgs, w_center, w_width)
        else:
            warnings.warn(
                "Could not determine windowing from DICOM metadata. Using full dynamic "
                "range instead.",
                UserWarning,
            )

    # Normalize
    imgs = _normalize(imgs).astype(np.uint8)

    # Determine output file path
    out_path = Path(out_path)
    if out_path.suffix not in SUPPORTED_FORMATS:
        raise ValueError(
            f"Unsupported output format: {out_path.suffix}. Supported formats are "
            f"{SUPPORTED_FORMATS}"
        )
    if not out_path.parent.exists():
        out_path.parent.mkdir(parents=True, exist_ok=True)

    # Determine frame duration
    if duration is None:
        try:
            duration = series.get_frame_duration()
        except AttributeError:
            warnings.warn(
                "Frame duration is not specified and could not be determined from "
                "DICOM data. Using 100 ms instead.",
                UserWarning,
            )
            duration = 100
        if duration <= 0 or duration > 10000:
            warnings.warn(
                f"Determined frame duration {duration} ms is out of range. Using 100 "
                f"ms instead.",
                UserWarning,
            )
            duration = 100

    # Write file
    imgs_pil = [Image.fromarray(img) for img in imgs]
    imgs_pil[0].save(
        out_path,
        save_all=True,
        append_images=imgs_pil[1:],
        duration=duration,
        loop=0,
    )


def _apply_windowing(arr: np.ndarray, center: float, width: float) -> np.ndarray:
    w_min = center - width / 2
    w_max = center + width / 2
    return np.clip(arr, w_min, w_max)


def _normalize(arr: np.ndarray) -> np.ndarray:
    w_min = arr.min()
    w_max = arr.max()
    if (w_max - w_min) == 0:
        return np.zeros_like(arr)
    return (arr - w_min) / (w_max - w_min) * 255.0
