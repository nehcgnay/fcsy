import os
import pytest

boto3 = pytest.importorskip("boto3")

from tempfile import mkdtemp
from shutil import rmtree
import pandas as pd
import numpy as np
from moto import mock_s3
from fcsy.fcs import Fcs
from fcsy.parser import create_open_func, S3Parser
from fcsy import DataFrame


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
        self.channels = ["a", "b", "c", "d"]
        self.long_channels = ["A", "B", "C", "D"]

        self.mock_s3.start()
        # you can use boto3.client('s3') if you prefer
        self.s3 = boto3.client("s3", region_name="us-east-1")
        self.s3.create_bucket(Bucket=self.bucket_name)

    def teardown_method(self):
        self.mock_s3.stop()

    def test_read_text_segment(self):
        with TmpDir() as dir_:
            filename = os.path.join(dir_, "test.fcs")
            cols = pd.MultiIndex.from_tuples(
                list(zip(self.channels, self.long_channels)),
                names=["short", "long"],
            )
            df = DataFrame(self.data, columns=cols)
            df.to_fcs(filename)

            self.s3.upload_file(filename, self.bucket_name, "test.fcs")

            parse_func = create_open_func(
                S3Parser, bucket=self.bucket_name, region_name="us-east-1"
            )

            with parse_func("test.fcs") as fp:
                seg = Fcs.read_text_segment(fp)
            assert seg.pnn == self.channels
            assert seg.pns == self.long_channels

    def test_from_fcs(self):
        with TmpDir() as dir_:
            filename = os.path.join(dir_, "test.fcs")
            cols = pd.MultiIndex.from_tuples(
                list(zip(self.channels, self.long_channels)),
                names=["short", "long"],
            )
            df = DataFrame(self.data, columns=cols)
            df.to_fcs(filename)

            self.s3.upload_file(filename, self.bucket_name, "test.fcs")
            parse_func = create_open_func(
                S3Parser, bucket=self.bucket_name, region_name="us-east-1"
            )

            with parse_func("test.fcs") as fp:
                fcs = Fcs.from_file(fp)
                assert fcs.short_channels == self.channels
                assert fcs.long_channels == self.long_channels
                assert fcs.count == len(self.data)
                assert np.array_equal(fcs.values, self.data)
