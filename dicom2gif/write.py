import warnings
from pathlib import Path

import numpy as np
from PIL import Image

from .cine import Cine

SUPPORTED_FORMATS = [".gif", ".apng", ".tiff", ".tif"]


def write_gif(
    cine: Cine,
    out_file: str | Path,
    duration: int | None = None,
    windowing: tuple[int, int] | str | None = None,
) -> None:
    """Save a Cine series as a GIF/APNG/TIFF file.

    Args:
        cine (Cine): Cine object to write.
        out_file (str | Path): Output file path. The file extension determines
            the file format. Allowed extensions are .gif, .apng, and .tiff/.tif.
        duration (int | None): Duration of each frame in milliseconds. If None,
            determined from the DICOM data. Defaults to None.
        windowing (tuple[int, int] | str | None): Either tuple of ints for
            window center and width, 'auto' for full dynamic range, or None. If
            None, uses window center and width from DICOM metadata. Defaults to
            None.
    """
    # Validate arguments
    if duration is not None and duration <= 0:
        raise ValueError(
            f"Duration must be None or a positive integer but was {duration}"
        )
    if windowing is not None and not (
        windowing == "auto" or (isinstance(windowing, tuple) and len(windowing) == 2)
    ):
        raise ValueError(
            "Windowing must be None, 'auto', or a tuple of (center, width)"
        )

    imgs = cine.pixel_array
    if len(imgs.shape) == 2:
        imgs = imgs[None, :, :]
        warnings.warn(
            "Pixel array has only two dimensions. Interpreting as a single frame.",
            UserWarning,
        )

    # Apply windowing
    windowing = windowing or cine.windowing
    if isinstance(windowing, tuple):
        w_center, w_width = windowing
        w_min = w_center - w_width / 2
        w_max = w_center + w_width / 2
    else:
        w_min = imgs.min()
        w_max = imgs.max()
    imgs = np.clip(imgs, w_min, w_max)
    imgs = (imgs - w_min) / (w_max - w_min) * 255.0
    imgs = imgs.astype(np.uint8)

    # Determine output file path
    out_file = Path(out_file)
    if out_file.suffix not in SUPPORTED_FORMATS:
        raise ValueError(
            f"Unsupported output format: {out_file.suffix}. "
            f"Supported formats are: {SUPPORTED_FORMATS}"
        )
    if not out_file.parent.exists():
        out_file.parent.mkdir(parents=True, exist_ok=True)

    # Save as GIF
    duration = duration or cine.duration
    if duration is None:
        warnings.warn(
            "Frame duration is not specified and could not be determined from "
            "DICOM data. Defaulting to 100 ms.",
            UserWarning,
        )
        duration = 100
    imgs_pil = [Image.fromarray(img) for img in imgs]
    imgs_pil[0].save(
        out_file,
        save_all=True,
        append_images=imgs_pil[1:],
        duration=duration,
        loop=0,
    )
