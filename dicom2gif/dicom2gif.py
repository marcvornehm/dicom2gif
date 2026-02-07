import warnings
from pathlib import Path

from .io import read_dcm, read_dir, write
from .series import DicomSeries


def dicom2gif(
    dcm_path: str | Path,
    pattern: str = "*.dcm",
    out_file: str | Path | None = None,
    format: str = "gif",
    duration: int | None = None,
    windowing: tuple[int, int] | str = "dicom",
) -> None:
    """Convert DICOM series to GIF format.
    Args:
        dcm_path (str | Path): Input DICOM file or directory containing DICOM
            files.
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
        windowing (tuple[int, int] | str): Either tuple of ints for window
            center and width, 'full' for full dynamic range, or 'dicom'. If
            'dicom', uses window center and width from DICOM metadata. Defaults
            to 'dicom'.
    """

    dcm_path = Path(dcm_path)
    format = format.lower().strip(".")
    all_series: dict[Path, DicomSeries]

    if dcm_path.is_file():
        if out_file is not None:
            out_file = Path(out_file)
        else:
            out_file = dcm_path.with_suffix(f".{format}")
        series = read_dcm(dcm_path)
        all_series = {out_file: series}

    elif dcm_path.is_dir():
        if out_file is not None:
            warnings.warn(
                "`out_file` is ignored when `dcm_path` is a directory.",
                UserWarning,
            )

        all_series = read_dir(dcm_path, pattern=pattern)
        if len(all_series) == 0:
            print(f"No DICOM series found in directory {dcm_path}.")
            return
        all_series = {p.with_suffix(f".{format}"): s for p, s in all_series.items()}

    else:
        raise ValueError(f"`dcm_path` must be a file or directory but was {dcm_path}")

    for out_file, series in all_series.items():
        write(series, out_file, duration=duration, windowing=windowing)
        print(f"Wrote {out_file}")
