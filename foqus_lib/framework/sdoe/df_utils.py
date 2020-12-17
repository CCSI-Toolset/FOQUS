import pandas as pd


def write(fname, df, index=False):
    # write data frame as csv file
    df.to_csv(fname, index=index)  # do not write row names


def load(fname, index=None):
    # load file as data frame
    df = pd.read_csv(fname)
    df.rename(columns=lambda x: x.strip(), inplace=True)
    if index:
        df.set_index(index, inplace=True)
    return df


def merge(fnames):
    # merge multiple files into single data frame

    if not fnames:
        return []

    dfs = [load(fname) for fname in fnames]

    if len(dfs) == 1:
        return dfs[0]

    df = pd.concat(dfs, join='inner', ignore_index=True)
    df = df.drop_duplicates()  # remove duplicate rows
    return df


def check(cfiles, hfiles):
    # aggregate files and ensure consistent columns

    cand_df = merge(cfiles)
    if not hfiles:
        return cand_df, []

    hist_df = merge(hfiles)

    cols = cand_df.columns.tolist()
    hist_df = hist_df[cols]

    return cand_df, hist_df
