__version__ = "0.10.0"

import pandas as pd
from copy import deepcopy
import warnings
from typing import Union
from .fcs import Fcs
from ._typing import ReadFcsBuffer, WriteFcsBuffer, UpdateFcsBuffer


__all__ = [
    "DataFrame",
    "Fcs",
    "write_fcs",
    "read_fcs",
    "read_fcs_names",
    "read_channels",
    "read_events_num",
    "rename_channels",
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

    def to_fcs(self, filepath_or_buffer: Union[str, WriteFcsBuffer]):

        """
        write fcs.

        :param filepath_or_buffer:
            String, or file-like object implementing a ``write()`` function.
            The string could be a s3 url with the format:
            ``s3://{bucket}/{key}``.
        :type param filepath_or_buffer: str or file-like object
        """

        long_channels = None
        if isinstance(self.columns, pd.MultiIndex):
            short_channels = self.columns.get_level_values("short").values
            long_channels = self.columns.get_level_values("long").values
        else:
            short_channels = self.columns

        Fcs(self.values, short_channels, long_channels).export(filepath_or_buffer)

    @classmethod
    def from_fcs(
        cls, filepath_or_buffer: Union[str, ReadFcsBuffer], channel_type: str = "short"
    ):
        """
        Read dataframe from fcs.

        :param filepath_or_buffer: str or file-like object.
            String, or file-like object implementing a ``read()`` function.
            The string could be a s3 url with the format:
            ``s3://{bucket}/{key}``.
        :type filepath_or_buffer: str or file-like object
        :param channel_type: {"short", "long", "multi"}, defaults to "short".
            "short" and "long" refer to short ($PnN) and long ($PnS) name of parameter n, respectively.
            See FCS3.1 data standard for detailed explanation.
        :type channel_type: str, optional
        :return: the dataframe contains the fcs channels and data
        :rtype: DataFrame
        """

        fcs = Fcs.from_file(filepath_or_buffer)
        colmap = {
            "short": fcs.short_channels,
            "long": fcs.long_channels,
            "multi": pd.MultiIndex.from_tuples(
                list(zip(fcs.short_channels, fcs.long_channels)),
                names=["short", "long"],
            ),
        }
        return DataFrame(fcs.values, columns=colmap[channel_type])


def read_channels(
    filepath_or_buffer: Union[str, ReadFcsBuffer], channel_type: str = "short"
) -> Union[list, pd.MultiIndex]:
    """
    Read fcs channels.

    :param filepath_or_buffer: String, or file-like object implementing a ``read()`` function.
            The string could be a s3 url with the format:
            ``s3://{bucket}/{key}``.
    :type filepath_or_buffer: str or file-like object
    :param channel_type: {"short", "long", "multi"}, defaults to "short".
        "short" and "long" refer to short ($PnN) and long ($PnS) name of parameter n, respectively.
        See FCS3.1 data standard for detailed explanation.
    :type channel_type: str, optional
    :return: list of the channels
    :rtype: Union[list, pd.MultiIndex]
    """

    fseg = Fcs.read_text_segment(filepath_or_buffer)
    maps = {
        "short": fseg.pnn,
        "long": fseg.pns,
        "multi": pd.MultiIndex.from_tuples(
            list(zip(fseg.pnn, fseg.pns)),
            names=["short", "long"],
        ),
    }
    return maps[channel_type]


def rename_channels(
    filepath_or_buffer: Union[str, UpdateFcsBuffer],
    channels: dict,
    channel_type: str,
    allow_rewrite: bool = False,
) -> None:
    """
    Rename fcs channels.

    :param filepath_or_buffer: String, or file-like object implementing both ``read()`` and ``write()`` functions.
            S3 url is not supported.
    :type filepath_or_buffer: str or file-like object
    :param channels: A mapper from old names to new names.
    :type channels: dict
    :param channel_type: {"short", "long"}.
        "short" and "long" refer to short ($PnN) and long ($PnS) name of parameter n, respectively.
        See FCS3.1 data standard for detailed explanation.
    :type channel_type: str
    :param allow_rewrite: Allow rewriting the whole file if channel only editing is not feasible.
        It can be one of the following:

        * The new channel names are too long causing Text Segment overlap with Data Segment.
        * filepath_or_buffer is s3 url.
    :type allow_rewrite: bool
    """
    tseg = Fcs.read_text_segment(filepath_or_buffer)
    tseg_old = deepcopy(tseg)
    {"short": tseg.update_pnn, "long": tseg.update_pns}[channel_type](channels)
    hseg = Fcs.read_header_segment(filepath_or_buffer)
    hseg.text_start = tseg.text_start
    hseg.text_end = tseg.text_end
    try:
        if tseg.text_end >= hseg.data_start:
            if allow_rewrite:
                dseg = Fcs.read_data_segment(filepath_or_buffer, hseg, tseg_old)
                Fcs(dseg.values, tseg.pnn, tseg.pns).export(filepath_or_buffer)
                return
            else:
                raise ValueError(
                    "New channel names are too long causing overlap with Data Segment."
                )
        Fcs.write_header_segment(filepath_or_buffer, hseg)
        Fcs.write_text_segment(filepath_or_buffer, tseg)
    except ValueError as e:
        if str(e) == "invalid s3 buffer mode":
            if allow_rewrite:
                dseg = Fcs.read_data_segment(filepath_or_buffer, hseg, tseg_old)
                Fcs(dseg.values, tseg.pnn, tseg.pns).export(filepath_or_buffer)
                return
            else:
                raise ValueError("S3 url is only supported when allow_rewrite is set.")
        else:
            raise e


def read_events_num(filepath_or_buffer: Union[str, ReadFcsBuffer]) -> int:
    """
    Read fcs events number.

    :param filepath_or_buffer: str or file-like object
            String, or file-like object implementing a ``read()`` function.
            The string could be a s3 url with the format:
            ``s3://{bucket}/{key}``.
    :type path: str
    :return: the events number
    :rtype: int
    """

    fseg = Fcs.read_text_segment(filepath_or_buffer)
    return fseg.tot
