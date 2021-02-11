import os
from tempfile import mkdtemp
from shutil import rmtree
import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal
from fcsy import DataFrame, read_channels, read_events_num, read_fcs, write_fcs


class TmpDir:
    def __enter__(self):
        self._tmp_dir_path = mkdtemp()
        return self._tmp_dir_path

    def __exit__(self, type, value, traceback):
        rmtree(self._tmp_dir_path)


class TestDataFrame:
    def setup_method(self):
        self.name = "test.fcs"
        self.data = np.array(
            [[1.1, 2.1, 3.1, 4.0011], [11.1, 12.1, 13.1, 14.0011]], dtype=np.float32
        )
        self.short_channels = ["a_di", "b_di", "c_di", "d_di"]
        self.long_channels = ["A A", "B B", "C C", "D D"]

    def test_io(self):
        with TmpDir() as dir_:
            filename = os.path.join(dir_, self.name)
            df = DataFrame(
                self.data,
                columns=pd.MultiIndex.from_tuples(
                    zip(self.short_channels, self.long_channels),
                    names=["short", "long"],
                ),
            )
            df.to_fcs(filename)
            df = DataFrame.from_fcs(filename, "multi")
            np.testing.assert_array_equal(df.values, self.data)
            np.testing.assert_array_equal(
                df.columns,
                pd.MultiIndex.from_tuples(
                    zip(self.short_channels, self.long_channels),
                    names=["short", "long"],
                ),
            )

    def test_read_fcs(self):
        with TmpDir() as dir_:
            filename = os.path.join(dir_, self.name)
            df = DataFrame(self.data, columns=self.short_channels)
            df.to_fcs(filename)
            df2 = read_fcs(filename)
            assert_frame_equal(df, df2)

    def test_write_fcs(self):
        with TmpDir() as dir_:
            filename = os.path.join(dir_, self.name)
            df = DataFrame(self.data, columns=self.short_channels)
            write_fcs(df, filename, long_names=self.long_channels)
            df = DataFrame.from_fcs(filename, "multi")
            np.testing.assert_array_equal(df.values, self.data)
            np.testing.assert_array_equal(
                df.columns,
                pd.MultiIndex.from_tuples(
                    zip(self.short_channels, self.long_channels),
                    names=["short", "long"],
                ),
            )

    def test_read_events_num(self):
        with TmpDir() as dir_:
            filename = os.path.join(dir_, self.name)
            df = DataFrame(self.data, columns=self.short_channels)
            write_fcs(df, filename, long_names=self.long_channels)
            num = read_events_num(filename)
            assert num == 2

    def test_read_channels(self):
        with TmpDir() as dir_:
            filename = os.path.join(dir_, self.name)
            df = DataFrame(self.data, columns=self.short_channels)
            write_fcs(df, filename, long_names=self.long_channels)

            assert read_channels(filename, "short") == self.short_channels
            assert read_channels(filename, "long") == self.long_channels
            np.testing.assert_array_equal(
                read_channels(filename, "multi"),
                pd.MultiIndex.from_tuples(
                    zip(self.short_channels, self.long_channels),
                    names=["short", "long"],
                ),
            )
