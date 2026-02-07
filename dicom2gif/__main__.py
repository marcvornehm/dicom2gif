import argparse

from .dicom2gif import dicom2gif


def windowing_argument(value: str) -> tuple[int, int] | str:
    if value.lower() in ["dicom", "full"]:
        return value.lower()
    try:
        wc, ww = map(int, value.split(","))
        return (wc, ww)
    except ValueError:
        raise argparse.ArgumentTypeError(
            "Windowing must be 'dicom', 'full', or two comma-separated integers"
        )


def frame_range_argument(value: str) -> tuple[int | None, int | None]:
    """Parse frame range argument.

    Accepts:
    - Single number: '5' -> (5, 5)
    - Range: '10-20' -> (10, 20)
    - Open start: '-20' -> (None, 20)
    - Open end: '10-' -> (10, None)
    """
    if "-" not in value:
        # Single frame number
        try:
            frame_num = int(value)
            return (frame_num, frame_num)
        except ValueError:
            raise argparse.ArgumentTypeError(
                f"Frame range must be a number or range like '10-20', got '{value}'"
            )

    parts = value.split("-", 1)
    try:
        start = int(parts[0]) if parts[0] else None
        end = int(parts[1]) if parts[1] else None
        return (start, end)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Frame range must be a number or range like '10-20', got '{value}'"
        )


def main() -> None:
    """Main function for CLI execution."""
    parser = argparse.ArgumentParser(
        description="Convert DICOM series to GIF/APNG/TIFF format."
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
        default="dicom",
        type=windowing_argument,
        help="Either two comma-separated integers for window center and width or "
        "'dicom' (uses window center and width from DICOM metadata) or 'full' (uses "
        "full dynamic range) for windowing modes. Defaults to 'dicom'.",
    )
    parser.add_argument(
        "--frames",
        default=None,
        type=frame_range_argument,
        help="Frame range to include in output (1-based, inclusive). Examples: '5' "
        "(frame 5 only), '10-20' (frames 10 to 20), '10-' (frame 10 to end), '-20' "
        "(start to frame 20). If not provided, all frames are included.",
    )

    args = parser.parse_args()

    frame_start, frame_end = args.frames if args.frames else (None, None)

    dicom2gif(
        dcm_path=args.dcm_path,
        pattern=args.pattern,
        out_file=args.out_file,
        format=args.format,
        duration=args.duration,
        windowing=args.windowing,
        frame_start=frame_start,
        frame_end=frame_end,
    )


if __name__ == "__main__":
    main()
