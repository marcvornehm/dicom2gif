from datetime import datetime
from typing import Any, Iterable

import numpy as np
import numpy.typing as npt
import pydicom
import pydicom.datadict


class DicomSeries:
    def __init__(self, dcms: Iterable[pydicom.Dataset] | pydicom.Dataset) -> None:
        if isinstance(dcms, pydicom.Dataset):
            dcms = [dcms]
        self._dcms = pydicom.Sequence(
            sorted(dcms, key=lambda x: (x.AcquisitionDateTime, x.InstanceNumber))
        )
        self._cache: dict[str | tuple[str, ...], Any] = {}
        self.SeriesInstanceUID = self._get_common_value_for_tag("SeriesInstanceUID")
        if self.SamplesPerPixel != 1:
            raise NotImplementedError("Only single channel images are supported.")

    def __getattr__(self, name: str) -> Any:
        # intercept DICOM keywords
        tag = pydicom.datadict.tag_for_keyword(name)
        if tag is None:  # None means `name` isn't a DICOM element keyword
            raise AttributeError
        return self._get_common_value_for_tag(name)

    def _get_common_value_for_tag(self, *tags: str) -> Any:
        if tags in self._cache:
            return self._cache[tags]

        values = self._get_all_values_for_tag(*tags)
        if any(v != values[0] for v in values[1:]):
            raise AttributeError(f"Tag {tags} is not consistent across the series")

        self._cache[tags] = values[0]
        return values[0]

    def _get_all_values_for_tag(self, *tags: str) -> list[Any]:
        return self._get_all_values_for_tag_rec(self._dcms, *tags, flatten=False)

    @staticmethod
    def _get_all_values_for_tag_rec(
        dsets: pydicom.Sequence | Iterable[pydicom.Dataset], *tags: str, flatten: bool
    ) -> list[Any]:
        tag = tags[0]
        values = []
        for d in dsets:
            try:
                v = d[tag].value
            except KeyError:
                raise AttributeError(f"Tag {tag} missing in at least one dataset")
            if len(tags) > 1 and isinstance(v, pydicom.Sequence):
                v = DicomSeries._get_all_values_for_tag_rec(v, *tags[1:], flatten=True)
            if isinstance(v, list) and flatten:
                values.extend(v)
            else:
                values.append(v)
        return values

    @property
    def pixel_array(self) -> npt.NDArray:
        arrs = []
        for d in self._dcms:
            arr = d.pixel_array
            if arr.ndim == 2:
                arr = arr[None]  # add frame dimension
            elif arr.ndim != 3:
                raise ValueError(
                    f"Unexpected number of dimensions in pixel array: ndim={arr.ndim}"
                )
            if arr.shape[-2:] != (self.Rows, self.Columns):
                raise ValueError(
                    f"Unexpected pixel array shape: {arr.shape}. Expected ({self.Rows}, {self.Columns}) for "
                    f"Rows and Columns."
                )
            arrs.append(arr)
        return np.concatenate(arrs, axis=0)

    def is_phase(self) -> bool:
        # we DO NOT check the Phase Contrast tag (0018, 9014) because it is also YES for magnitude flow images
        try:
            return str(self.ComplexImageComponent) == "PHASE"
        except AttributeError:
            pass
        try:
            image_type = self.ImageType
            return any(t in image_type for t in ["P", "PHASE", "VELOCITY"])
        except AttributeError:
            pass
        return False

    def get_windowing(self) -> tuple[int, int] | None:
        """Get windowing parameters (center, width) for display."""
        if self.is_phase():
            ww = 2**self.BitsStored
            wc = ww // 2
            return (wc, ww)

        try:  # legacy
            wc = self._get_all_values_for_tag("WindowCenter")
            ww = self._get_all_values_for_tag("WindowWidth")
            return (int(np.mean(wc)), int(np.mean(ww)))
        except AttributeError:
            pass

        try:  # enhanced
            wc = self._get_all_values_for_tag(
                "PerFrameFunctionalGroupsSequence",
                "FrameVOILUTSequence",
                "WindowCenter",
            )
            ww = self._get_all_values_for_tag(
                "PerFrameFunctionalGroupsSequence",
                "FrameVOILUTSequence",
                "WindowWidth",
            )
            return (int(np.mean(wc)), int(np.mean(ww)))
        except AttributeError:
            pass

        return None

    def _get_timestamps(self) -> list[float]:
        try:  # legacy cine
            timestamps = self._get_all_values_for_tag("TriggerTime")
            timestamps = [float(t) for t in timestamps]
            return timestamps
        except AttributeError:
            pass

        try:  # enhanced cine
            timestamps = self._get_all_values_for_tag(
                "PerFrameFunctionalGroupsSequence",
                "CardiacSynchronizationSequence",
                "NominalCardiacTriggerDelayTime",
            )
            return timestamps[0]  # use times of first slice
        except AttributeError:
            pass

        try:  # others
            timestamps = self._get_all_values_for_tag("AcquisitionDateTime")
            timestamps = [datetime.strptime(ts, "%Y%m%d%H%M%S.%f") for ts in timestamps]
            d0 = datetime(timestamps[0].year, timestamps[0].month, timestamps[0].day)
            timestamps = [t - d0 for t in timestamps]
            timestamps = [t.total_seconds() * 1000.0 for t in timestamps]  # ms
            return timestamps
        except AttributeError:
            pass

        raise AttributeError("No timestamp information found in DICOM data.")

    def get_frame_duration(self) -> int:
        """Get frame duration in milliseconds."""
        timestamps = self._get_timestamps()
        if len(timestamps) < 2:
            raise AttributeError("Not enough timestamps to determine duration.")

        dt = np.diff(timestamps)
        dt = dt[dt > 0]  # filter out non-positive differences
        if len(dt) == 0:
            raise AttributeError(
                "No positive timestamp differences found to determine duration."
            )

        duration = float(dt.mean())
        duration = round(duration / 10) * 10  # round to nearest multiple of 10
        return duration
