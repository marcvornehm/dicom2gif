import warnings
from pathlib import Path

from .read import read_dcm, read_dir
from .write import write_gif


def dicom2gif(
    dcm_path: str | Path,
    pattern: str = "*.dcm",
    out_file: str | Path | None = None,
    format: str = "gif",
    duration: int | None = None,
    windowing: tuple[int, int] | str | None = None,
) -> None:
    """Convert DICOM cine series to GIF format.
    Args:
        dcm_path (str | Path): Input DICOM file or directory containing DICOM
            files. Can be an enhanced DICOM file, any frame of a legacy DICOM
            series, or a directory containing enhanced or legacy DICOMs or both.
        pattern (str): Glob pattern to match DICOM files when `dcm_path` is a
            directory. Defaults to '*.dcm'.
        out_file (str | Path | None): Output file path. If None, uses DICOM file
            path with extension given by `format`. If `dcm_path` is a directory,
            `out_file` is ignored. Defaults to None.
        format (str): Output format ('gif', 'apng', or 'tiff'). If `out_file` is
            not None, the format is inferred from its extension and `format` is
            ignored. Defaults to 'gif'.
        duration (int | None): Duration of each frame in milliseconds. If None,
            determined from the DICOM data. Defaults to None.
        windowing (tuple[int, int] | str | None): Either tuple of ints for
            window center and width, 'auto' for full dynamic range, or None. If
            None, uses window center and width from DICOM metadata. Defaults to
            None.
    """

    dcm_path = Path(dcm_path)
    format = format.lower().strip(".")
    if dcm_path.is_dir():
        cines = read_dir(dcm_path, pattern=pattern)
        if not cines:
            print(f"No cine series found.")
            return
        if out_file is not None:
            warnings.warn(
                "`out_file` is ignored when `dcm_path` is a directory.",
                UserWarning,
            )
        for path, cine in cines.items():
            out_file = path.with_suffix(f".{format}")
            write_gif(cine, out_file, duration=duration, windowing=windowing)
    else:
        cine = read_dcm(dcm_path)
        out_file = out_file or dcm_path.with_suffix(f".{format}")
        write_gif(cine, out_file, duration=duration, windowing=windowing)
