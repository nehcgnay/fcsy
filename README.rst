
.. image:: https://img.shields.io/pypi/v/fcsy.svg
    :target: https://pypi.python.org/pypi/fcsy
.. image:: https://readthedocs.org/projects/fcsy/badge/?version=latest
    :target: https://fcsy.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status
.. image:: https://img.shields.io/pypi/l/fcsy.svg
    :target: https://github.com/nehcgnay/fcsy/blob/master/LICENSE
.. image:: https://img.shields.io/pypi/dm/fcsy?style=flat-square
    :target: https://img.shields.io/pypi/dm/fcsy
.. image:: https://github.com/nehcgnay/fcsy/workflows/Python%20package/badge.svg
    :target: https://github.com/nehcgnay/fcsy/workflows/Python%20package
.. image:: https://github.com/nehcgnay/fcsy/workflows/Upload%20Python%20Package/badge.svg
    :target: https://github.com/nehcgnay/fcsy/workflows/Upload%20Python%20Package



fcsy: A package for processing FCS files.
-----------------------------------------

fcsy is developed based on `Data File Standard for Flow Cytometry Version FCS 3.1 <https://www.genepattern.org/attachments/fcs_3_1_standard.pdf>`_

Installation
------------

.. code-block:: console

    $ pip install fcsy

    
for working with s3: 

.. code-block:: console

    $ pip install fcsy[s3]


Usage
-----

Write and read fcs based on Dataframe
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

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
    
    >>> df.to_fcs('sample1.fcs')
    >>> df = DataFrame.from_fcs('sample1.fcs', channel_type='multi')
    >>> df
    short    a    b    c
    long     A    B    C
    0      1.0  2.0  3.0
    1      4.0  5.0  6.0
    
Work with fcs metadata
~~~~~~~~~~~~~~~~~~~~~~

Read fcs channels

.. code-block:: python

    >>> from fcsy import read_channels

    >>> read_channels('sample1.fcs', channel_type='multi')
    MultiIndex([('a', 'A'),
                ('b', 'B'),
                ('c', 'C')],
               names=['short', 'long'])

Rename channels

.. code-block:: python

    >>> from fcsy import rename_channels, read_channels

    >>> rename_channels('sample1.fcs', {'a': 'a_1', 'b': 'b_1'}, channel_type='short')
    >>> read_channels('sample1.fcs', channel_type='multi')
    MultiIndex([('a_1', 'A'),
                ('b_1', 'B'),
                (  'c', 'C')],
               names=['short', 'long'])
    

    >>> rename_channels('sample1.fcs', {'A': 'A_1', 'C': 'C_1'}, channel_type='long')
    >>> read_channels('sample1.fcs', channel_type='multi')
    MultiIndex([('a_1', 'A_1'),
                ('b_1',   'B'),
                (  'c', 'C_1')],
               names=['short', 'long'])
    
Read events number

.. code-block:: python

    >>> from fcsy import read_events_num

    >>> read_events_num('sample1.fcs')
    2

Work with files on aws s3
~~~~~~~~~~~~~~~~~~~~~~~~~
``Dataframe`` io, ``read_channels`` and ``read_events_num`` support 
s3 url with the format: ``s3://{bucket}/{key}``.
``rename_channles`` doesn't accept s3 url since file editing is not supported on s3.
Please rename the channels locally and re-upload for such functionality.

.. testsetup:: *
    
    >>> import boto3
    >>> from moto import mock_s3
    >>> mock = mock_s3()
    >>> mock.start()
    >>> s3 = boto3.client("s3", region_name="us-east-1")
    >>> _ = s3.create_bucket(Bucket='sample-bucket')

Write and read

.. code-block:: python

    >>> df.to_fcs('s3://sample-bucket/sample.fcs')
    >>> df.from_fcs('s3://sample-bucket/sample.fcs', channel_type='multi')
    short    a    b    c
    long     A    B    C
    0      1.0  2.0  3.0
    1      4.0  5.0  6.0

Read channels

.. code-block:: python

    >>> read_channels('s3://sample-bucket/sample.fcs', channel_type='multi')
    MultiIndex([('a', 'A'),
                ('b', 'B'),
                ('c', 'C')],
               names=['short', 'long'])

Read events number

.. code-block:: python

    >>> read_events_num('s3://sample-bucket/sample.fcs')
    2

.. testsetup:: *

    >>> mock.stop()




Documentation
-------------
The documentation is available on https://fcsy.readthedocs.io/

License
-------
-   Free software: MIT license


History
-------
Consult the Releases_ page for fixes and enhancements of each version.

.. _Releases: https://github.com/nehcgnay/fcsy/releases



