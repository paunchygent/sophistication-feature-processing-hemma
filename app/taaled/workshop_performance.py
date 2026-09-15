"""Bounded execution settings; not TAALED analysis options or a scheduler."""
from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Performance:
    batch_size: int = 64
    n_process: int = 1

    def __post_init__(self):
        if type(self.batch_size) is not int or not 1 <= self.batch_size <= 256:
            raise ValueError("TAALED batch size must be an integer from 1 to 256")
        if type(self.n_process) is not int or self.n_process not in (1, 2, 4):
            raise ValueError("TAALED process count must be 1, 2 or 4")
        available = len(os.sched_getaffinity(0))
        if self.n_process > max(1, available - 2):
            raise ValueError("Leave CPU affinity headroom for the desktop and parent worker")

    @classmethod
    def environment(cls):
        return cls(int(os.environ.get("TAALED_BATCH_SIZE", "64")),
                   int(os.environ.get("TAALED_N_PROCESS", "1")))
