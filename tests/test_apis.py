import os
from tempfile import mkdtemp
from shutil import rmtree
import numpy as np
from numpy.testing import assert_almost_equal
import pandas as pd
from pandas.testing import assert_frame_equal
import pytest
from fcsy import (
    DataFrame,
    read_channels,
    read_events_num,
    read_fcs,
    write_fcs,
    rename_channels,
)


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

    def test_rename_channels(self):
        with TmpDir() as dir_:
            df = DataFrame(
                self.data,
                columns=pd.MultiIndex.from_tuples(
                    zip(self.short_channels, self.long_channels),
                    names=["short", "long"],
                ),
            )
            filename = os.path.join(dir_, self.name)
            df.to_fcs(filename)
            rename_channels(
                filename, dict(zip(self.short_channels, list("abcd"))), "short"
            )
            short_channels = read_channels(filename, "short")
            assert short_channels == list("abcd")

            rename_channels(
                filename, dict(zip(self.long_channels, list("ABCD"))), "long"
            )
            long_channels = read_channels(filename, "long")
            assert long_channels == list("ABCD")

            data = [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]
            columns = pd.MultiIndex.from_tuples(
                list(zip("abc", "ABC")), names=["short", "long"]
            )
            df = DataFrame(data, columns=columns)
            filename = os.path.join(dir_, self.name)
            df.to_fcs(filename)
            rename_channels(
                filename, {"a": "a_1", "b": "b_1", "c": "c_1"}, channel_type="short"
            )
            short_channels = read_channels(filename, "short")
            long_channels = read_channels(filename, "long")
            assert short_channels == ["a_1", "b_1", "c_1"]
            assert long_channels == list("ABC")

    def test_rename_channels_alt(self):
        with TmpDir() as dir_:
            df = DataFrame(
                self.data,
                columns=pd.MultiIndex.from_tuples(
                    zip(self.short_channels, self.long_channels),
                    names=["short", "long"],
                ),
            )
            filename = os.path.join(dir_, self.name)
            df.to_fcs(filename)

            ln = ""
            for i in range(30):
                ln = ln + str(i)

            with pytest.raises(ValueError) as err:
                rename_channels(filename, {"a_di": ln}, "short")
            assert (
                str(err.value)
                == "New channel names are too long causing overlap with Data Segment."
            )

            rename_channels(filename, {"a_di": ln}, "short", allow_rewrite=True)
            df2 = DataFrame.from_fcs(filename)

            assert_almost_equal(df.values, df2.values)


class TestWithBuffer:
    def setup_method(self):
        self.name = "test.fcs"
        self.data = np.array(
            [[1.1, 2.1, 3.1, 4.0011], [11.1, 12.1, 13.1, 14.0011]], dtype=np.float32
        )
        self.short_channels = ["a", "b", "c", "d"]
        self.long_channels = ["A", "B", "C", "D"]

    def test_from_fcs(self):
        with TmpDir() as dir_:
            filename = os.path.join(dir_, "test.fcs")
            cols = pd.MultiIndex.from_tuples(
                list(zip(self.short_channels, self.long_channels)),
                names=["short", "long"],
            )
            df = DataFrame(self.data, columns=cols)
            df.to_fcs(filename)

            with open(filename, "rb") as fp:
                dfr = DataFrame.from_fcs(fp, channel_type="multi")
            assert_frame_equal(dfr, df)

    def test_to_fcs(self):
        with TmpDir() as dir_:
            filename = os.path.join(dir_, "test.fcs")
            cols = pd.MultiIndex.from_tuples(
                list(zip(self.short_channels, self.long_channels)),
                names=["short", "long"],
            )
            df = DataFrame(self.data, columns=cols)
            with open(filename, "wb") as fp:
                df.to_fcs(fp)

            dfr = DataFrame.from_fcs(filename, channel_type="multi")
            assert_frame_equal(df, dfr)

    def test_read_events_num(self):
        with TmpDir() as dir_:
            filename = os.path.join(dir_, "test.fcs")
            cols = pd.MultiIndex.from_tuples(
                list(zip(self.short_channels, self.long_channels)),
                names=["short", "long"],
            )
            df = DataFrame(self.data, columns=cols)
            df.to_fcs(filename)

            with open(filename, "rb") as fp:
                num = read_events_num(fp)
            assert num == len(self.data)

    def test_read_channels(self):
        with TmpDir() as dir_:
            filename = os.path.join(dir_, "test.fcs")
            cols = pd.MultiIndex.from_tuples(
                list(zip(self.short_channels, self.long_channels)),
                names=["short", "long"],
            )
            df = DataFrame(self.data, columns=cols)
            df.to_fcs(filename)

            assert read_channels(filename, "short") == self.short_channels
            assert read_channels(filename, "long") == self.long_channels
            np.testing.assert_array_equal(read_channels(filename, "multi"), cols)

    def test_rename_channels(self):
        with TmpDir() as dir_:
            filename = os.path.join(dir_, "test.fcs")
            cols = pd.MultiIndex.from_tuples(
                list(zip(self.short_channels, self.long_channels)),
                names=["short", "long"],
            )
            df = DataFrame(self.data, columns=cols)
            df.to_fcs(filename)

            with open(filename, "rb+") as fp:
                rename_channels(
                    fp, dict(zip(self.short_channels, list("wxyz"))), "short"
                )

            with open(filename, "rb+") as fp:
                rename_channels(fp, dict(zip(self.long_channels, list("WXYZ"))), "long")

            assert read_channels(filename, "short") == list("wxyz")
            assert read_channels(filename, "long") == list("WXYZ")
