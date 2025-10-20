from __future__ import annotations

import dataclasses
from functools import cached_property

import numpy as np
import pandas as pd


@dataclasses.dataclass
class Market:
    name: str
    prices: pd.Series[float]
    highest_price_across_next_n_hours: pd.Series[float]
    lowest_price_across_next_n_hours: pd.Series[float]
    interval_hours: float

    def interval_timedelta(self) -> pd.Timedelta:
        return pd.Timedelta(hours=self.interval_hours)

    def is_interval_start(self, *, timestamp: pd.Timestamp) -> bool:
        if self.interval_hours == 1.0:
            return bool(timestamp.minute == 0)
        elif self.interval_hours == 0.5:
            return timestamp.minute in (0, 30)
        return False

    @cached_property
    def average_price(self) -> float:
        return float(np.mean(list(self.prices)))
