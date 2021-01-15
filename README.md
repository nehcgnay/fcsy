# fcsy

<a href='https://pypi.python.org/pypi/fcsy'>
<img src=https://img.shields.io/pypi/v/fcsy.svg>
</a>
<image src=https://img.shields.io/pypi/dm/fcsy?style=flat-square>
<img src='https://github.com/nehcgnay/fcsy/workflows/Python%20package/badge.svg'>
<img src='https://github.com/nehcgnay/fcsy/workflows/Upload%20Python%20Package/badge.svg'>

A package for processing FCS files.

-   Free software: MIT license

## Installation

```bash
$ pip install fcsy
```

## Usage 

Use the pandas flavor api ```fcsy.DataFrame``` which 
has all the features of pandas DataFrame plus the fcs io (New in v0.5.0).

## API (ver >= 0.5.0)

### DataFrame.from_fcs(path, channel_type='short')
Read fcs file to dataframe

|              |                                          |
| ------------ | ---------------------------------------- |
| path         | path to the input fcs                    |
| channel_type | "short" \| "long" \| "multi". <br/> Read short or long channels to the dataframe columns. In "multi" mode both channels are read as a pandas MultiIndex          |
| return    | DataFrame |

Example:

```python
from fcsy import DataFrame

df = DataFrame.from_fcs('sample1.fcs', channel_type='multi')
```


### DataFrame.to_fcs(path)
Write dataframe to fcs file. 'short' and 'long' channels will be written separately if pandas MultiIndex is used as the columns. Otherwise 'short' and 'long' channels will be the same writen from the columns. 

Example:

```python
import numpy as np
from fcsy import DataFrame

df = DataFrame(np.random.rand(10, 4)), columns=list('ABCD'))
df.to_fcs('sample1.fcs')
```


## Old API 
Write a data frame to fcs. df.columns is written to both short and long names of the fcs.


```python
from fcsy import write_fcs

write_fcs(df, 'output_file')
```

Write to fcs with "long name". df.columns and long_names are written to short and long names of the fcs.

```python
write_fcs(df, 'output_file', long_names=['a','b','c'])
```

Read a fcs file to pandas DataFrame.

```python
from fcsy import read_fcs

df = read_fcs('input_file')
```

Read a fcs file with "long name"

```python
df = read_fcs('input_file', name_type='long')

# or only read the names
from fcsy import read_fcs_names

long_names = read_fcs_names('input_file', name_type='long')
```

Write a data frame to fcs. df.columns is written to both short and long names of the fcs.

```python
from fcsy import write_fcs

write_fcs(df, 'output_file')
```

Write to fcs with "long name". df.columns and long_names are written to short and long names of the fcs.

```python
write_fcs(df, 'output_file', long_names=['a','b','c'])
```

## Credits

This package was created with Cookiecutter* and the `audreyr/cookiecutter-pypackage`* project template.

`Cookiecutter`: https://github.com/audreyr/cookiecutter
`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
