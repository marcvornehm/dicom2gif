"""Main entry point for the dicom2gif module."""

import argparse

from .dicom2gif import dicom2gif


def windowing_argument(value: str) -> tuple[int, int] | str:
    if value.lower() == "auto":
        return "auto"
    try:
        wc, ww = map(int, value.split(","))
        return (wc, ww)
    except ValueError:
        raise argparse.ArgumentTypeError(
            "Windowing must be 'auto' or two comma-separated integers"
        )


def main() -> None:
    """Main function for CLI execution."""
    parser = argparse.ArgumentParser(
        description="Convert DICOM cine series to GIF format."
    )
    parser.add_argument(
        "dcm_path",
        type=str,
        help="Input DICOM file or directory containing DICOM files. Can be an enhanced "
        "DICOM file, any frame of a legacy DICOM series, or a directory containing "
        "enhanced or legacy DICOMs or both.",
    )
    parser.add_argument(
        "-p",
        "--pattern",
        default="*.dcm",
        type=str,
        help="Glob pattern to match DICOM files when `dcm_path` is a directory. "
        "Defaults to '*.dcm'.",
    )
    parser.add_argument(
        "-o",
        "--out_file",
        default=None,
        type=str,
        help="Output file path. If not provided, uses DICOM file path path with "
        "extension given by `format`. If `dcm_path` is a directory, `out_file` is "
        "ignored.",
    )
    parser.add_argument(
        "-f",
        "--format",
        default="gif",
        type=str,
        choices=["gif", "apng", "tiff"],
        help="Output format. If `out_file` is provided, the format is inferred from "
        "its extension and `format` is ignored. Defaults to 'gif'.",
    )
    parser.add_argument(
        "-d",
        "--duration",
        default=None,
        type=int,
        help="Duration per frame in milliseconds. If not provided, determined from the "
        "DICOM data.",
    )
    parser.add_argument(
        "-w",
        "--windowing",
        default=None,
        type=windowing_argument,
        help="Either two comma-separated integers for window center and width or "
        "'auto' for full dynamic range. If not provided, uses window center and width "
        "from DICOM metadata.",
    )

    args = parser.parse_args()
    dicom2gif(
        dcm_path=args.dcm_path,
        pattern=args.pattern,
        out_file=args.out_file,
        format=args.format,
        duration=args.duration,
        windowing=args.windowing,
    )


if __name__ == "__main__":
    main()
