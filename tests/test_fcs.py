#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from tempfile import mkdtemp
from shutil import rmtree
import numpy as np
import pandas as pd
from pandas.util.testing import assert_frame_equal
from fcsy.fcs import *


class TmpDir:
    def __enter__(self):
        self._tmp_dir_path = mkdtemp()
        return self._tmp_dir_path

    def __exit__(self, type, value, traceback):
        rmtree(self._tmp_dir_path)


class TestFCS:
    def setup_method(self):
        self.name = 'test.fcs'
        self.data = np.array([[1.1, 2.1, 3.1, 4.0011],
                              [11.1, 12.1, 13.1, 14.0011]], dtype=np.float32)
        self.channels = ['a', 'b', 'c', 'd']
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

        chn = ['a', 'b']
        data = np.array([[1, 2], [11, 12]])
        with TmpDir() as dir_:
            filename = os.path.join(dir_, self.name)
            self.fcs_writer.export(filename, data, chn)
            data_copy = self.fcs_reader.data(filename)
            assert np.array_equal(data_copy, data)


class TestFcsWriter:
    def setup_method(self):
        self.name = 'test.fcs'
        self.data = np.array([[1.1, 2.1, 3.1, 4.0011],
                              [11.1, 12.1, 13.1, 14.0011],
                              [21.1, 22.1, 23.1, 24.0011]])
        self.channels = ['a', 'b', 'c', 'd']
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
        assert headsg[:6].decode('ASCII') == 'FCS3.1'
        assert headsg[6:].decode('UTF-8') == ' ' * 4

    def test_export(self):
        with TmpDir() as dir_:
            filename = os.path.join(dir_, self.name)
            self.fcs_writer.export(filename, self.data, self.channels, list('wxyz'))
            fcs_header_seg = self.fcs_reader._analyze_header(filename)
            fcs_vars, fcs_deli = self.fcs_reader._analyze_text(filename, fcs_header_seg.text_start,
                                                               fcs_header_seg.text_end)
            assert fcs_header_seg.data_start == int(fcs_vars['$BEGINDATA'])
            assert fcs_header_seg.data_end == int(fcs_vars['$ENDDATA'])

            assert self.fcs_reader.long_header(filename) == self.channels
            assert self.fcs_reader.header(filename) == list('wxyz')

    def _test_export2(self):
        channel = ['Time', 'Event_length', 'Y89Di', 'Pd102Di', 'Rh103Di', 'Pd104Di',
                   'Pd105Di', 'Pd106Di', 'Pd108Di', 'Cd110Di', 'Pd110Di', 'Cd112Di',
                   'In113Di', 'In115Di', 'I127Di', 'La139Di', 'Ce140Di', 'Pr141Di',
                   'Nd142Di', 'Nd143Di', 'Nd144Di', 'Nd145Di', 'Nd146Di', 'Sm147Di',
                   'Nd148Di', 'Sm149Di', 'Nd150Di', 'Eu151Di', 'Sm152Di', 'Eu153Di',
                   'Sm154Di', 'Gd155Di', 'Gd156Di', 'Gd157Di', 'Gd158Di', 'Tb159Di',
                   'Gd160Di', 'Dy161Di', 'Dy162Di', 'Dy163Di', 'Dy164Di', 'Ho165Di',
                   'Er166Di', 'Er167Di', 'Er168Di', 'Tm169Di', 'Er170Di', 'Yb171Di',
                   'Yb172Di', 'Yb173Di', 'Yb174Di', 'Lu175Di', 'Yb176Di', 'Ir191Di',
                   'Ir193Di', 'Pt195Di', 'Bi209Di']

        c3 = ['Time', 'Event_length', 'CD45', 'Pd102Di', 'Rh103Di', 'Pd104Di',
              'Pd105Di', 'Pd106Di', 'Pd108Di', 'Cd110Di', 'Pd110Di', 'Cd112Di',
              'In113Di', 'CD57', 'I127Di', 'La139Di', 'EQBeads', 'CCR6', 'CD19',
              'CD5', 'CD16', 'CD4', 'CD8a', 'CD11c', 'CD31', 'Sm149Di', 'Nd150Di',
              'CD123', 'abTCR', 'EQBeads', 'CD3e', 'Gd155Di', 'Gd156Di', 'CXCR3',
              'Gd158Di', 'Tb159Di', 'CD14', 'CD161', 'Dy162Di', 'HLA-DR', 'CD44',
              'CD127', 'Er166Di', 'CD27', 'CD38', 'CD45RA', 'CD20', 'Yb171Di',
              'IgD', 'CD56', 'CXCR5', 'EQBeads', 'Yb176Di', 'DNAIr', 'DNAIr',
              'Cisplatin', 'Bi209Di']

        c2 = ['Time', 'Event_length', 'CD45', 'Pd102Di', 'Rh103Di', 'Pd104Di',
              'Pd105Di', 'Pd106Di', 'Pd108Di', 'Cd110Di', 'Pd110Di', 'Cd112Di',
              'In113Di', 'In115Di', 'I127Di', 'La139Di', 'EQBeads', 'Pr141Di',
              'Nd142Di', 'Nd143Di', 'Nd144Di', 'Nd145Di', 'Nd146Di', 'Sm147Di',
              'Nd148Di', 'Sm149Di', 'CD64', 'Eu151Di', 'Sm152Di', 'CD13', 'CD3e',
              'Gd155Di', 'Gd156Di', 'CD9', 'Gd158Di', 'Tb159Di', 'CD14',
              'Dy161Di', 'CD29', 'Dy163Di', 'Dy164Di', 'Ho165Di', 'Er166Di',
              'Er167Di', 'Er168Di', 'Tm169Di', 'Er170Di', 'Yb171Di', 'Yb172Di',
              'Yb173Di', 'Yb174Di', 'Lu175Di', 'Yb176Di', 'DNAIr', 'DNAIr',
              'Pt195Di', 'Bi209Di']

        # print(c2[13], c3[13])
        # c2[13] = c3[13]

        f = '/Users/yang/Documents/test3.csv'
        df = pd.read_csv(f)
        data = df.values

        with TmpDir() as dir_:
            filename = os.path.join(dir_, self.name)
            self.fcs_writer.export(filename, data, channel, c2)
            fcs_header_seg = self.fcs_reader._analyze_header(filename)
            fcs_vars, fcs_deli = self.fcs_reader._analyze_text(filename, fcs_header_seg.text_start,
                                                               fcs_header_seg.text_end)

            # self.assertEqual(fcs_header_seg.data_start, int(fcs_vars['$BEGINDATA']))
            # self.assertEqual(fcs_header_seg.data_end, int(fcs_vars['$ENDDATA']))

            assert self.fcs_reader.long_header(filename) == channel
            assert self.fcs_reader.header(filename) == c2
            expected_data = np.array(self.fcs_reader.data(filename))
            np.testing.assert_array_almost_equal(data, expected_data)



