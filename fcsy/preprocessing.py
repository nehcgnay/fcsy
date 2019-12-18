import numpy as np
import pandas as pd


def zscore(df, axis=0, ddof=0):
    a = np.asanyarray(df)
    mns = a.mean(axis=axis)
    sstd = a.std(axis=axis, ddof=ddof)
    if axis and mns.ndim < a.ndim:
        f = (a - np.expand_dims(mns, axis=axis))
        t = np.expand_dims(sstd, axis=axis)
        x = f/t
    else:
        x = (a - mns) / sstd
    return pd.DataFrame(x, columns=df.columns, index=df.index)


def arcsinh(df, factor=5):
    df = df / factor
    return df.apply(np.arcsinh)


def rm_outliers(df, threshold=0.05, **kwargs):
    df = df.copy()
    num = int(df.shape[0] * threshold)
    for c in df:
        if c in kwargs:
            num = int(df.shape[0] * kwargs[c])
        ind = np.argsort(df[c].values)
        df.loc[ind[:num], c] = df.loc[ind[num], c]
        df.loc[ind[-num:], c] = df.loc[ind[-num - 1], c]
    return df


def randomize(df, factor=0.5):
    return df.applymap(lambda x: np.random.normal(x, factor))
