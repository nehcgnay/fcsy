#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import pytest
from tempfile import mkdtemp
from shutil import rmtree
import numpy as np
from mock import patch
import pandas as pd
from pandas.testing import assert_frame_equal
from fcsy import *


class TmpDir:
    def __enter__(self):
        self._tmp_dir_path = mkdtemp()
        return self._tmp_dir_path

    def __exit__(self, type, value, traceback):
        rmtree(self._tmp_dir_path)


@patch("fcsy.fcs.FcsWriter")
def test_write_fcs(MockWriter):
    writer = MockWriter()
    data = np.array([[1, 2], [3, 4]])
    short_names = list("ab")
    df = pd.DataFrame(data, columns=short_names)
    fout = "test.fcs"
    write_fcs(df, fout)

    called_args = writer.export.call_args[0]

    assert called_args[0] == fout
    np.testing.assert_array_equal(called_args[1], data)
    np.testing.assert_array_equal(called_args[2], short_names)
    np.testing.assert_array_equal(called_args[3], short_names)

    long_names = list("AB")
    write_fcs(df, fout, long_names=long_names)
    called_args = writer.export.call_args[0]
    assert called_args[0] == fout
    np.testing.assert_array_equal(called_args[1], data)
    np.testing.assert_array_equal(called_args[2], long_names)
    np.testing.assert_array_equal(called_args[3], short_names)


@patch("fcsy.fcs.FcsReader")
def test_read_fcs_names(MockReader):
    name = "test.fcs"
    data = np.array(
        [[1.1, 2.1, 3.1, 4.0011], [11.1, 12.1, 13.1, 14.0011]], dtype=np.float32
    )
    channels = ["a", "b", "c", "d"]
    long_channels = ["A", "B", "C", "D"]
    fcs_writer = FcsWriter()

    with TmpDir() as dir_:
        filename = os.path.join(dir_, name)
        fcs_writer.export(
            filename, data, long_channels, channels
        )

        names = read_fcs_names(filename, "short")
        np.testing.assert_array_equal(names, channels)

        names = read_fcs_names(filename, "long")
        np.testing.assert_array_equal(names, long_channels)

        with pytest.raises(KeyError) as err:
            read_fcs_names(filename, "XX")


@patch("fcsy.fcs.read_fcs_names")
@patch("fcsy.fcs.FcsReader")
def test_read_fcs(MockReader, mock_read_fcs_names):
    reader = MockReader()
    data = np.array([[1, 2], [3, 4]])
    short_names = list("ab")
    long_names = list("AB")
    reader.data.return_value = data
    mock_read_fcs_names.return_value = short_names

    df = read_fcs("f", "short")

    reader.data.assert_called_with("f")
    mock_read_fcs_names.assert_called_with("f", name_type="short")
    np.testing.assert_array_equal(df.values, data)
    np.testing.assert_array_equal(df.columns, short_names)

    mock_read_fcs_names.return_value = long_names
    df = read_fcs("f", "long")

    reader.data.assert_called_with("f")
    mock_read_fcs_names.assert_called_with("f", name_type="long")
    np.testing.assert_array_equal(df.values, data)
    np.testing.assert_array_equal(df.columns, long_names)


class TestFCS:
    def setup_method(self):
        self.name = "test.fcs"
        self.data = np.array(
            [[1.1, 2.1, 3.1, 4.0011], [11.1, 12.1, 13.1, 14.0011]], dtype=np.float32
        )
        self.channels = ["a", "b", "c", "d"]
        self.long_channels = ["A", "B", "C", "D"]
        self.fcs_writer = FcsWriter()

    def test_header(self):
        with TmpDir() as dir_:
            filename = os.path.join(dir_, self.name)
            self.fcs_writer.export(filename, self.data, self.channels)
            fcs = Fcs(filename)
            assert fcs.short_channels == self.channels

    def test_count(self):
        with TmpDir() as dir_:
            filename = os.path.join(dir_, self.name)
            self.fcs_writer.export(filename, self.data, self.channels)
            fcs = Fcs(filename)
            assert fcs.count == len(self.data)

    def test_data(self):
        with TmpDir() as dir_:
            filename = os.path.join(dir_, self.name)
            self.fcs_writer.export(filename, self.data, self.channels)
            fcs = Fcs(filename)
            assert np.array_equal(fcs.read_data(), self.data)

        chn = ["a", "b"]
        data = np.array([[1, 2], [11, 12]])
        with TmpDir() as dir_:
            filename = os.path.join(dir_, self.name)
            self.fcs_writer.export(filename, data, chn)
            fcs = Fcs(filename)
            assert np.array_equal(fcs.read_data(), data)

    def test_dataframe(self):
        with TmpDir() as dir_:
            filename = os.path.join(dir_, self.name)
            self.fcs_writer.export(
                filename, self.data, self.long_channels, self.channels
            )
            fcs = Fcs(filename)
            df = fcs.to_dataframe()
            np.testing.assert_array_equal(df.values, self.data)
            np.testing.assert_array_equal(
                df.columns,
                pd.MultiIndex.from_tuples(
                    zip(self.channels, self.long_channels), names=["short", "long"]
                ),
            )

    def test_from_fcs(self):
        with TmpDir() as dir_:
            filename = os.path.join(dir_, self.name)
            self.fcs_writer.export(
                filename, self.data, self.long_channels, self.channels
            )
            df = DataFrame.from_fcs(filename, 'multi')
            np.testing.assert_array_equal(df.values, self.data)
            np.testing.assert_array_equal(
                df.columns,
                pd.MultiIndex.from_tuples(
                    zip(self.channels, self.long_channels), names=["short", "long"]
                ),
            )

    def test_to_fcs(self):
        df = DataFrame(self.data, columns=self.channels)
        with TmpDir() as dir_:
            filename = os.path.join(dir_, 'export.fcs')
            df.to_fcs(filename)

            fcs = Fcs(filename)
            df2 = fcs.to_dataframe(channel_type='short')

        assert_frame_equal(df, df2)


class TestFCSReader:
    def setup_method(self):
        self.name = "test.fcs"
        self.data = np.array(
            [[1.1, 2.1, 3.1, 4.0011], [11.1, 12.1, 13.1, 14.0011]], dtype=np.float32
        )
        self.channels = ["a", "b", "c", "d"]
        self.fcs_writer = FcsWriter()
        self.fcs_reader = FcsReader()

    def test_header(self):
        with TmpDir() as dir_:
            filename = os.path.join(dir_, self.name)
            self.fcs_writer.export(filename, self.data, self.channels)
            channels = self.fcs_reader.header(filename)
            assert channels == self.channels

    def test_count(self):
        with TmpDir() as dir_:
            filename = os.path.join(dir_, self.name)
            self.fcs_writer.export(filename, self.data, self.channels)
            num = self.fcs_reader.count(filename)
            assert num == len(self.data)

    def test_data(self):
        with TmpDir() as dir_:
            filename = os.path.join(dir_, self.name)
            self.fcs_writer.export(filename, self.data, self.channels)
            data = self.fcs_reader.data(filename)
            assert np.array_equal(data, self.data)

        chn = ["a", "b"]
        data = np.array([[1, 2], [11, 12]])
        with TmpDir() as dir_:
            filename = os.path.join(dir_, self.name)
            self.fcs_writer.export(filename, data, chn)
            data_copy = self.fcs_reader.data(filename)
            assert np.array_equal(data_copy, data)


class TestFcsWriter:
    def setup_method(self):
        self.name = "test.fcs"
        self.data = np.array(
            [
                [1.1, 2.1, 3.1, 4.0011],
                [11.1, 12.1, 13.1, 14.0011],
                [21.1, 22.1, 23.1, 24.0011],
            ]
        )
        self.channels = ["a", "b", "c", "d"]
        self.fcs_writer = FcsWriter()
        self.fcs_reader = FcsReader()

    def test_cal_datapos(self):
        textend = 2
        datasize = 8
        start_expected = 4
        end_expected = 11
        start, end = self.fcs_writer.cal_datapos(textend, datasize)
        assert start == start_expected
        assert end == end_expected

        textend = 999
        datasize = 9000
        start_expected = 1007
        end_expected = 10006
        start, end = self.fcs_writer.cal_datapos(textend, datasize)
        assert start == start_expected
        assert end == end_expected

    def test_build_headsg(self):
        headsg = self.fcs_writer.build_headsg()
        assert headsg[:6].decode("ASCII") == "FCS3.1"
        assert headsg[6:].decode("UTF-8") == " " * 4

    def test_export(self):
        with TmpDir() as dir_:
            filename = os.path.join(dir_, self.name)
            self.fcs_writer.export(filename, self.data, self.channels, list("wxyz"))
            with open(filename, "rb") as fp:
                fcs_header_seg = self.fcs_reader._analyze_header(fp)
                fp.seek(fcs_header_seg.text_start)
                fcs_vars, fcs_deli = self.fcs_reader._analyze_text(
                    fp, fcs_header_seg.text_start, fcs_header_seg.text_end
                )
                assert fcs_header_seg.data_start == int(fcs_vars["$BEGINDATA"])
                assert fcs_header_seg.data_end == int(fcs_vars["$ENDDATA"])

                assert self.fcs_reader.long_header(filename) == self.channels
                assert self.fcs_reader.header(filename) == list("wxyz")
