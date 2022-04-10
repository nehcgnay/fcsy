import os
import pytest
from tempfile import mkdtemp
from shutil import rmtree
import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal
from fcsy import (
    DataFrame,
    read_channels,
    read_events_num,
    read_fcs,
    write_fcs,
    rename_channels,
)

try:
    import boto3
    from moto import mock_s3
except ImportError:
    boto3 = None
    mock_s3 = None


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


@pytest.mark.skipif(boto3 is None, reason="requires module boto3")
class TestWithS3:
    mock_s3 = mock_s3()
    bucket_name = "test-bucket"

    def setup_method(self):
        self.name = "test.fcs"
        self.data = np.array(
            [[1.1, 2.1, 3.1, 4.0011], [11.1, 12.1, 13.1, 14.0011]], dtype=np.float32
        )
        self.short_channels = ["a", "b", "c", "d"]
        self.long_channels = ["A", "B", "C", "D"]

        self.mock_s3.start()
        self.s3 = boto3.client("s3", region_name="us-east-1")
        self.s3.create_bucket(Bucket=self.bucket_name)

    def teardown_method(self):
        self.mock_s3.stop()

    def test_from_fcs(self):
        with TmpDir() as dir_:
            filename = os.path.join(dir_, "test.fcs")
            cols = pd.MultiIndex.from_tuples(
                list(zip(self.short_channels, self.long_channels)),
                names=["short", "long"],
            )
            df = DataFrame(self.data, columns=cols)
            df.to_fcs(filename)

            self.s3.upload_file(filename, self.bucket_name, "test.fcs")

            dfr = DataFrame.from_fcs(
                f"s3://{self.bucket_name}/test.fcs", channel_type="multi"
            )
            assert_frame_equal(dfr, df)

    def test_to_fcs(self):
        with TmpDir() as dir_:
            cols = pd.MultiIndex.from_tuples(
                list(zip(self.short_channels, self.long_channels)),
                names=["short", "long"],
            )
            df = DataFrame(self.data, columns=cols)
            df.to_fcs(f"s3://{self.bucket_name}/test.fcs")
            filename = os.path.join(dir_, "test.fcs")
            self.s3.download_file(self.bucket_name, "test.fcs", filename)

            dfr = DataFrame.from_fcs(filename, channel_type="multi")
            assert_frame_equal(df, dfr)

    def test_read_events_num(self):
        df = DataFrame(self.data, columns=self.short_channels)
        s3_file_path = f"s3://{self.bucket_name}/test.fcs"
        df.to_fcs(s3_file_path)

        num = read_events_num(s3_file_path)
        assert num == len(self.data)

    def test_read_channels(self):
        cols = pd.MultiIndex.from_tuples(
            list(zip(self.short_channels, self.long_channels)),
            names=["short", "long"],
        )
        df = DataFrame(self.data, columns=cols)
        s3_file_path = f"s3://{self.bucket_name}/test.fcs"
        df.to_fcs(s3_file_path)
        assert read_channels(s3_file_path, "short") == self.short_channels
        assert read_channels(s3_file_path, "long") == self.long_channels
        np.testing.assert_array_equal(read_channels(s3_file_path, "multi"), cols)

    def test_rename_channels(self):
        cols = pd.MultiIndex.from_tuples(
            list(zip(self.short_channels, self.long_channels)),
            names=["short", "long"],
        )
        df = DataFrame(self.data, columns=cols)
        s3_file_path = f"s3://{self.bucket_name}/test.fcs"
        df.to_fcs(s3_file_path)

        with pytest.raises(ValueError) as e:
            rename_channels(
                s3_file_path, dict(zip(self.short_channels, list("abcd"))), "short"
            )
        assert (
            str(e.value)
            == "S3 url is not supported. Rename the channels locally and re-upload."
        )
