
.. image:: https://img.shields.io/pypi/v/fcsy.svg
    :target: https://pypi.python.org/pypi/fcsy
.. image:: https://readthedocs.org/projects/fcsy/badge/?version=latest
        :target: https://fcsy.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status
.. image:: https://img.shields.io/pypi/dm/fcsy?style=flat-square
.. image:: https://github.com/nehcgnay/fcsy/workflows/Python%20package/badge.svg
.. image:: https://github.com/nehcgnay/fcsy/workflows/Upload%20Python%20Package/badge.svg



fcsy: A package for processing FCS files.
-----------------------------------------


Installation
------------

.. code-block:: console

    $ pip install fcsy


Usage
-----

Read a fcs

.. code-block:: python

    from fcsy import DataFrame

    df = DataFrame.from_fcs('sample1.fcs', channel_type='multi')


Write a dataframe to fcs

.. code-block:: python

    import numpy as np
    from fcsy import DataFrame

    df = DataFrame(np.random.rand(10, 4), columns=list('ABCD'))
    df.to_fcs('sample1.fcs')


Read fcs channels without data

.. code-block:: python

    from fcsy import read_channels

    read_channels('sample1.fcs', channel_type='multi')


Read events number

.. code-block:: python

    from fcsy import read_events_num

    read_events_num('sample1.fcs')

License
-------
-   Free software: MIT license


History
-------
Consult the Releases_ page for fixes and enhancements of each version.

.. _Releases: https://github.com/nehcgnay/fcsy/releases



