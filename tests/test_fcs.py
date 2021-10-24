#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from tempfile import mkdtemp
from shutil import rmtree
import numpy as np
from fcsy import DataFrame
from fcsy.fcs import *


class TmpDir:
    def __enter__(self):
        self._tmp_dir_path = mkdtemp()
        return self._tmp_dir_path

    def __exit__(self, type, value, traceback):
        rmtree(self._tmp_dir_path)


class TestFCS:
    def setup_method(self):
        self.name = "test.fcs"
        self.data = np.array(
            [[1.1, 2.1, 3.1, 4.0011], [11.1, 12.1, 13.1, 14.0011]], dtype=np.float32
        )
        self.channels = ["a", "b", "c", "d"]
        self.long_channels = ["A", "B", "C", "D"]

    def test_header(self):
        with TmpDir() as dir_:
            filename = os.path.join(dir_, self.name)
            df = DataFrame(self.data, columns=self.channels)
            df.to_fcs(filename)
            fcs = Fcs.from_file(filename)
            assert fcs.short_channels == self.channels

    def test_count(self):
        with TmpDir() as dir_:
            filename = os.path.join(dir_, self.name)
            df = DataFrame(self.data, columns=self.channels)
            df.to_fcs(filename)
            fcs = Fcs.from_file(filename)
            assert fcs.count == len(self.data)

    def test_data(self):
        with TmpDir() as dir_:
            filename = os.path.join(dir_, self.name)
            df = DataFrame(self.data, columns=self.channels)
            df.to_fcs(filename)
            fcs = Fcs.from_file(filename)
            assert np.array_equal(fcs.values, self.data)

    def test_export(self):
        with TmpDir() as dir_:
            filename = os.path.join(dir_, "export.fcs")
            text_start = 256
            fseg = TextSegment(
                self.data.shape[0],
                self.long_channels,
                self.channels,
                self.data.max(axis=0),
                text_start=text_start,
            )
            header = HeaderSegment(
                text_start, fseg.text_end, fseg.data_start, fseg.data_end
            )
            data = DataSegment(
                self.data,
                fseg.datatype,
                self.data.shape[1],
                self.data.shape[0],
                fseg.endian,
            )
            fcs = Fcs(self.data, self.long_channels, self.channels)
            fcs.export(filename)

            with open(filename, "rb") as fp:
                assert fp.read(58).decode("UTF-8") == header.to_string()
                fp.seek(text_start)
                assert (
                    fp.read(header.text_end - fseg.text_start + 1)
                    .decode("UTF-8")
                    .strip()
                    == fseg.to_string()
                )
                fp.seek(fseg.data_start)
                dseg = DataSegment.from_string(
                    fp.read(fseg.data_end - fseg.data_start + 1),
                    fseg.datatype,
                    len(fseg.pnn),
                    fseg.tot,
                    fseg.endian,
                )
                assert np.array_equal(dseg.values, self.data)


class TestTextSegment:
    def setup_method(self):
        self.name = "test.fcs"
        self.data = np.array(
            [[1.1, 2.1, 3.1, 4.0011], [11.1, 12.1, 13.1, 14.0011]], dtype=np.float32
        )
        self.channels = ["a", "b", "c", "d"]
        self.long_channels = ["A", "B", "C", "D"]

    def test_locations(self):
        fseg = TextSegment(
            self.data.shape[0],
            self.long_channels,
            self.channels,
            self.data.max(axis=0),
            data_start=1000,
        )
        assert fseg.text_start == 256
        assert fseg.text_end == 564
        assert fseg.data_start == 1000
        assert fseg.data_end == 0

    def test_data_pos(self):
        assert TextSegment.cal_datapos(10, 100) == (14, 113)

    def test_dict_to_string(self):
        text = {}
        text["BEGINDATA"] = "256"
        text["BYTEORD"] = "1,2,3,4"  # little endian
        assert (
            TextSegment.dict_to_string(text, "/") == "/$BEGINDATA/256/$BYTEORD/1,2,3,4/"
        )

    def test_from_string(self):
        with open('tests/TextSegment.txt', 'rb') as fp:
            s = fp.readline()

        fseq = TextSegment.from_string(s)
        assert fseq.data_start == 4064
        assert fseq.data_end == 119207043

    def test_cal_max_text_ends(self):
        assert TextSegment.cal_max_text_ends({}, "/", 0) == 124

    def test_cal_datapos(self):
        textend = 2
        datasize = 8
        start_expected = 4
        end_expected = 11
        start, end = TextSegment.cal_datapos(textend, datasize)
        assert start == start_expected
        assert end == end_expected

        textend = 999
        datasize = 9000
        start_expected = 1007
        end_expected = 10006
        start, end = TextSegment.cal_datapos(textend, datasize)
        assert start == start_expected
        assert end == end_expected


class TestHeaderSegment:
    def setup_method(self):
        self.name = "test.fcs"
        self.data = np.array(
            [[1.1, 2.1, 3.1, 4.0011], [11.1, 12.1, 13.1, 14.0011]], dtype=np.float32
        )
        self.channels = ["a", "b", "c", "d"]
        self.long_channels = ["A", "B", "C", "D"]

    def test_to_string(self):
        header = HeaderSegment(256, 561, 563, 99999999, 0, 0)
        assert (
            header.to_string()
            == "FCS3.1         256     561     56399999999       0       0"
        )

        header = HeaderSegment(256, 561, 563, 100000000, 0, 0)
        assert (
            header.to_string()
            == "FCS3.1         256     561       0       0       0       0"
        )

    def test_from_string(self):
        s = b"FCS3.1         256     561     563     789    1000    2000"
        header = HeaderSegment.from_string(s)
        assert header.asdict() == dict(
            text_start=256,
            text_end=561,
            data_start=563,
            data_end=789,
            analysis_start=1000,
            analysis_end=2000,
        )
        assert header.ver == "FCS3.1"


class TestDataSegment:
    def setup_method(self):
        self.name = "test.fcs"
        self.data = np.array(
            [[1.1, 2.1, 3.1, 4.0011], [11.1, 12.1, 13.1, 14.0011]], dtype=np.float32
        )
        self.channels = ["a", "b", "c", "d"]
        self.long_channels = ["A", "B", "C", "D"]

    def test_to_string(self):
        data = DataSegment(self.data, "f", self.data.shape[1], self.data.shape[0], "<")
        assert (
            data.to_string()
            == b"\xcd\xcc\x8c?ff\x06@ffF@\x03\t\x80@\x9a\x991A\x9a\x99AA\x9a\x99QA\x81\x04`A"
        )

    def test_from_string(self):
        s = b"\xcd\xcc\x8c?ff\x06@ffF@\x03\t\x80@\x9a\x991A\x9a\x99AA\x9a\x99QA\x81\x04`A"
        data = DataSegment.from_string(
            s, "f", self.data.shape[1], self.data.shape[0], "<"
        )
        np.testing.assert_array_equal(data.values, self.data)
