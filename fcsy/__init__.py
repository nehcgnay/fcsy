__version__ = '0.6.0'

import pandas as pd
import warnings
from .fcs import Fcs


__all__ = [
    "DataFrame",
    "Fcs",
    "write_fcs",
    "read_fcs",
    "read_fcs_names",
    "read_channels",
]


def read_fcs_names(f, name_type="short"):
    warnings.warn(
        "read_fcs_names() is deprecated; use read_channels()",
        DeprecationWarning,
    )
    fcs = Fcs.from_file(f)
    mapping = {"short": fcs.short_channels, "long": fcs.long_channels}
    return mapping[name_type]


def read_fcs(f, name_type="short"):
    warnings.warn(
        "read_fcs() is deprecated; use DataFrame.from_fcs()",
        DeprecationWarning,
    )
    return DataFrame.from_fcs(f, channel_type=name_type)


def write_fcs(df: pd.DataFrame, path: str, long_names=None):
    warnings.warn(
        "write_fcs() is deprecated; use DataFrame.export()",
        DeprecationWarning,
    )
    fcs = Fcs(df.values, df.columns, long_names)
    fcs.export(path)


class DataFrame(pd.DataFrame):
    @property
    def _constructor(self):
        return DataFrame

    def to_fcs(self, path):
        long_channels = None
        if isinstance(self.columns, pd.MultiIndex):
            short_channels = self.columns.get_level_values("short").values
            long_channels = self.columns.get_level_values("long").values
        else:
            short_channels = self.columns

        Fcs(self.values, short_channels, long_channels).export(path)

    @classmethod
    def from_fcs(cls, path, channel_type="short"):
        fcs = Fcs.from_file(path)
        colmap = {
            "short": fcs.short_channels,
            "long": fcs.long_channels,
            "multi": pd.MultiIndex.from_tuples(
                list(zip(fcs.short_channels, fcs.long_channels)),
                names=["short", "long"],
            ),
        }
        return DataFrame(fcs.values, columns=colmap[channel_type])


def read_channels(path: str, channel_type: str):
    fseg = Fcs.read_text_segment(path)
    maps = {
        "short": fseg.pnn,
        "long": fseg.pns,
        "multi": pd.MultiIndex.from_tuples(
            list(zip(fseg.pnn, fseg.pns)),
            names=["short", "long"],
        ),
    }
    return maps[channel_type]


def read_events_num(path: str):
    fseg = Fcs.read_text_segment(path)
    return fseg.tot