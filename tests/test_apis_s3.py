import os
import pytest

boto3 = pytest.importorskip("boto3")
from moto import mock_s3
from tempfile import mkdtemp
from shutil import rmtree
import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal
from fcsy import (
    DataFrame,
    read_channels,
    read_events_num,
    rename_channels,
)


class TmpDir:
    def __enter__(self):
        self._tmp_dir_path = mkdtemp()
        return self._tmp_dir_path

    def __exit__(self, type, value, traceback):
        rmtree(self._tmp_dir_path)


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

    def test_rename_channels_alt(self):
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
        assert str(e.value) == "S3 url is only supported when allow_rewrite is set."

        ln = ""
        for i in range(30):
            ln = ln + str(i)
        with pytest.raises(ValueError) as e:
            rename_channels(s3_file_path, {"c": ln}, "short")
        assert (
            str(e.value)
            == "New channel names are too long causing overlap with Data Segment."
        )

    def test_rename_channels(self):
        cols = pd.MultiIndex.from_tuples(
            list(zip(self.short_channels, self.long_channels)),
            names=["short", "long"],
        )
        df = DataFrame(self.data, columns=cols)
        s3_file_path = f"s3://{self.bucket_name}/test.fcs"
        df.to_fcs(s3_file_path)

        rename_channels(
            s3_file_path, {"a": "a_1", "d": "d_1"}, "short", allow_rewrite=True
        )

        dfr = DataFrame.from_fcs(s3_file_path, channel_type="multi")

        np.testing.assert_array_equal(
            ["a_1", "b", "c", "d_1"],
            dfr.columns.get_level_values("short").values,
        )
        np.testing.assert_array_equal(
            list("ABCD"),
            dfr.columns.get_level_values("long").values,
        )

        ln = ""
        for i in range(30):
            ln = ln + str(i)
        rename_channels(s3_file_path, {"C": ln}, "long", allow_rewrite=True)
        assert ["A", "B", ln, "D"] == read_channels(s3_file_path, "long")
