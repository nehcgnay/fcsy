[![image](https://img.shields.io/pypi/v/fcsy.svg?style=flat-square)](https://pypi.python.org/pypi/fcsy)
[![image](https://img.shields.io/pypi/l/fcsy.svg?style=flat-square)](https://github.com/nehcgnay/fcsy/blob/master/LICENSE)
[![image](https://readthedocs.org/projects/fcsy/badge/?version=latest&style=flat-square)](https://fcsy.readthedocs.io/en/latest/?badge=latest)
[![image](https://img.shields.io/pypi/dm/fcsy?style=flat-square)](https://img.shields.io/pypi/dm/fcsy)
[![image](https://img.shields.io/pypi/pyversions/fcsy?style=flat-square)](https://img.shields.io/pypi/pyversions/fcsy)

# fcsy: Python package for processing FCS

fcsy is developed based on [Data File Standard for Flow Cytometry Version FCS 3.1](https://www.genepattern.org/attachments/fcs_3_1_standard.pdf)

# Installation

```console
$ pip install fcsy
```

for working with s3:

```console
$ pip install fcsy[s3]
```

# Usage

## Write and read fcs based on Dataframe

```python
>>> import pandas as pd
>>> from fcsy import DataFrame

>>> data = [[1.0,2.0,3.0],[4.0,5.0,6.0]]
>>> columns = pd.MultiIndex.from_tuples(list(zip('abc', 'ABC')), names=["short", "long"])
>>> df = DataFrame(data, columns=columns)
>>> df
short    a    b    c
long     A    B    C
0      1.0  2.0  3.0
1      4.0  5.0  6.0

>>> df.to_fcs('sample.fcs')
>>> df = DataFrame.from_fcs('sample.fcs', channel_type='multi')
>>> df
short    a    b    c
long     A    B    C
0      1.0  2.0  3.0
1      4.0  5.0  6.0
```

## Work with fcs metadata

Read fcs channels

```python
>>> from fcsy import read_channels

>>> read_channels('sample.fcs', channel_type='multi')
MultiIndex([('a', 'A'),
            ('b', 'B'),
            ('c', 'C')],
           names=['short', 'long'])
```

Rename channels

```python
>>> from fcsy import rename_channels, read_channels

>>> rename_channels('sample.fcs', {'a': 'a_1', 'b': 'b_1'}, channel_type='short')
>>> read_channels('sample.fcs', channel_type='multi')
MultiIndex([('a_1', 'A'),
            ('b_1', 'B'),
            (  'c', 'C')],
           names=['short', 'long'])


>>> rename_channels('sample.fcs', {'A': 'A_1', 'C': 'C_1'}, channel_type='long')
>>> read_channels('sample.fcs', channel_type='multi')
MultiIndex([('a_1', 'A_1'),
            ('b_1',   'B'),
            (  'c', 'C_1')],
           names=['short', 'long'])
```

Read events number

```python
>>> from fcsy import read_events_num

>>> read_events_num('sample.fcs')
2
```

## Work with files on aws s3

All apis support s3 url with the format: `s3://{bucket}/{key}`.

<!-- >>> import boto3
>>> from moto import mock_s3
>>> mock = mock_s3()
>>> mock.start()
>>> s3 = boto3.client("s3", region_name="us-east-1")
>>> _ = s3.create_bucket(Bucket='sample-bucket') -->
Write and read

```python
>>> df.to_fcs('s3://sample-bucket/sample.fcs')
>>> df.from_fcs('s3://sample-bucket/sample.fcs', channel_type='multi')
short    a    b    c
long     A    B    C
0      1.0  2.0  3.0
1      4.0  5.0  6.0
```

Read channels

```python
>>> read_channels('s3://sample-bucket/sample.fcs', channel_type='multi')
MultiIndex([('a', 'A'),
            ('b', 'B'),
            ('c', 'C')],
           names=['short', 'long'])
```

Read events number

```python
>>> read_events_num('s3://sample-bucket/sample.fcs')
2
```

<!-- >>> mock.stop() -->
# Documentation

The documentation is available on [https://fcsy.readthedocs.io/](https://fcsy.readthedocs.io/)

# License


* Free software: MIT license

# History

Consult the [Releases](https://github.com/nehcgnay/fcsy/releases) page for fixes and enhancements of each version.
