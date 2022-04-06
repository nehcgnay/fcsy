__version__ = "0.9.0"

import pandas as pd
import warnings
from typing import Union
from .fcs import Fcs


__all__ = [
    "DataFrame",
    "Fcs",
    "write_fcs",
    "read_fcs",
    "read_fcs_names",
    "read_channels",
    "read_events_num",
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

    def to_fcs(self, path: str):

        """
        write fcs

        :param path: path to the fcs
        :type path: str
        """

        long_channels = None
        if isinstance(self.columns, pd.MultiIndex):
            short_channels = self.columns.get_level_values("short").values
            long_channels = self.columns.get_level_values("long").values
        else:
            short_channels = self.columns

        Fcs(self.values, short_channels, long_channels).export(path)

    @classmethod
    def from_fcs(cls, path: str, channel_type: str = "short"):
        """
        Read dataframe from fcs

        :param path: path to the fcs
        :type path: str
        :param channel_type: {"short", "long", "multi"}, defaults to "short".
            "short" and "long" refer to short ($PnN) and long ($PnS) name of parameter n, respectively.
            See FCS3.1 data standard for detailed explanation.
        :type channel_type: str, optional
        :return: the dataframe contains the fcs channels and data
        :rtype: DataFrame
        """

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


def read_channels(path: str, channel_type: str = "short") -> Union[list, pd.MultiIndex]:
    """
    Read the fcs channels (without data)

    :param path: path to the fcs
    :type path: str
    :param channel_type: {"short", "long", "multi"}, defaults to "short".
        "short" and "long" refer to short ($PnN) and long ($PnS) name of parameter n, respectively.
        See FCS3.1 data standard for detailed explanation.

    :type channel_type: str, optional
    :return: list of the channels
    :rtype: Union[list, pd.MultiIndex]
    """

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


def read_events_num(path: str) -> int:
    """
    Read the fcs events number

    :param path: path to the fcs
    :type path: str
    :return: the events number
    :rtype: int
    """

    fseg = Fcs.read_text_segment(path)
    return fseg.tot
