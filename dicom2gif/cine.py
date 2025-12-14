import warnings
from abc import ABC, abstractmethod
from typing import Iterable

import numpy as np
import numpy.typing as npt
import pydicom


class Cine(ABC):
    @property
    def duration(self) -> int | None:
        """Get frame duration in milliseconds."""
        try:
            dur = self._get_duration()
            if dur <= 0:
                return None
            return dur
        except AttributeError:
            warnings.warn("Could not determine frame duration.", UserWarning)
            return None

    @property
    @abstractmethod
    def pixel_array(self) -> npt.NDArray:
        """Get pixel array with shape (frames, height, width)."""
        pass

    @property
    @abstractmethod
    def is_phase(self) -> bool:
        """Check if this is a phase/velocity image."""
        pass

    @property
    @abstractmethod
    def bits_stored(self) -> int:
        """Get number of bits stored per pixel."""
        pass

    @property
    def windowing(self) -> tuple[int, int] | None:
        """Get windowing parameters (center, width) for display."""
        if self.is_phase:
            w_width = 2**self.bits_stored
            w_center = w_width // 2
            return (w_center, w_width)
        try:
            return self._get_windowing()
        except AttributeError:
            warnings.warn(
                "Could not determine window width. Defaulting to full range.",
                UserWarning,
            )
            return None

    @abstractmethod
    def _get_trigger_times(self) -> npt.NDArray[np.float32]:
        pass

    def _get_duration(self) -> int:
        tt = self._get_trigger_times()
        if len(tt) < 2:
            raise AttributeError("Not enough trigger times to determine duration.")
        duration = float(np.diff(tt).mean())
        duration = round(duration / 10) * 10  # round to nearest multiple of 10
        return duration

    @abstractmethod
    def _get_windowing(self) -> tuple[int, int]:
        pass

    @staticmethod
    def _is_phase(dcm: pydicom.FileDataset) -> bool:
        try:
            return str(dcm.ComplexImageComponent) == "PHASE"
        except AttributeError:
            pass
        try:
            image_type = dcm.ImageType
            return any(t in image_type for t in ["P", "PHASE", "VELOCITY"])
        except AttributeError:
            pass
        return False


class CineEnhanced(Cine):
    def __init__(self, dcm: pydicom.FileDataset) -> None:
        self.dcm = dcm

    @property
    def pixel_array(self) -> npt.NDArray:
        return self.dcm.pixel_array

    @property
    def is_phase(self) -> bool:
        return self._is_phase(self.dcm)

    @property
    def bits_stored(self) -> int:
        return int(self.dcm.BitsStored)

    def _get_windowing(self) -> tuple[int, int]:
        win = self.dcm.PerFrameFunctionalGroupsSequence[0].FrameVOILUTSequence[0]
        return (int(win.WindowCenter), int(win.WindowWidth))

    def _get_trigger_times(self) -> npt.NDArray[np.float32]:
        return np.array([
            float(f.CardiacSynchronizationSequence[0].NominalCardiacTriggerDelayTime)
            for f in self.dcm.PerFrameFunctionalGroupsSequence
        ])  # fmt: skip


class CineLegacy(Cine):
    def __init__(self, dcm: Iterable[pydicom.FileDataset]) -> None:
        self.dcm = sorted(dcm, key=lambda x: (x.ContentTime, x.InstanceNumber))

    @property
    def pixel_array(self) -> npt.NDArray:
        return np.stack([d.pixel_array for d in self.dcm], axis=0)

    @property
    def is_phase(self) -> bool:
        return self._is_phase(self.dcm[0])

    @property
    def bits_stored(self) -> int:
        return int(self.dcm[0].BitsStored)

    def _get_windowing(self) -> tuple[int, int]:
        return (int(self.dcm[0].WindowCenter), int(self.dcm[0].WindowWidth))

    def _get_trigger_times(self) -> npt.NDArray[np.float32]:
        return np.array([float(d.TriggerTime) for d in self.dcm])
