====
fcsy
====


.. image:: https://img.shields.io/pypi/v/fcsy.svg
        :target: https://pypi.python.org/pypi/fcsy

.. image:: https://img.shields.io/travis/nehcgnay/fcsy.svg
        :target: https://travis-ci.org/nehcgnay/fcsy



A package for processing FCS files.


* Free software: MIT license

Installation
------------
.. code:: python

    pip install fcsy


Usage
-----

Read a fcs file to pandas DataFrame.

.. code:: python

    import fcsy

    df = fcsy.read_fcs('input_file')

Read a fcs file with "long name"

.. code:: python

    df = fcsy.read_fcs('input_file', name_type='long')

    # or only read the names

    long_names = fcsy.read_fcs_names('input_file', name_type='long')


Write a data frame to fcs. df.columns is written to both short and long names of the fcs.

.. code:: python

    fcsy.write_fcs(df, 'output_file')


Write to fcs with "long name". df.columns and long_names are written to short and long names of the fcs.

.. code:: python

    fcsy.write_fcs(df, 'output_file', long_names=['a','b','c'])




Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
