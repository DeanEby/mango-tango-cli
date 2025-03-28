from collections import Counter
from itertools import accumulate

import polars as pl

from mango_tango_cib.analyzer_interface.context import PrimaryAnalyzerContext

from .interface import (
    COL_AUTHOR_ID,
    COL_HASHTAGS,
    COL_TIME,
    OUTPUT_COL_COUNT,
    OUTPUT_COL_GINI,
    OUTPUT_COL_HASHTAGS,
    OUTPUT_GINI,
)

# let's look at the hashtags column
COLS_ALL = [COL_AUTHOR_ID, COL_TIME, COL_HASHTAGS]

NULL_CHAR = "[]"  # this is taken as the null character for hashtags


def gini(x):
    """
    Parameters
    ----------
    x : list[str]
        List of values for which to compute the Gini coefficient

    Returns
    -------
    float
        Gini coefficient
    """
    x_counts = Counter(x).values()

    sorted_x = sorted(x_counts)
    n = len(sorted_x)
    cumx = list(accumulate(sorted_x))

    return (n + 1 - 2 * sum(cumx) / cumx[-1]) / n


def main(context: PrimaryAnalyzerContext):

    input_reader = context.input()
    df_input = input_reader.preprocess(pl.read_parquet(input_reader.parquet_path))

    # assign None to messages with no hashtags
    df_input = df_input.with_columns(
        pl.when(pl.col(COL_HASHTAGS) == NULL_CHAR)
        .then(None)
        .otherwise(
            pl.col(COL_HASHTAGS)
            .str.strip_chars("[]")
            .str.replace_all("'", "")
            .str.replace_all(" ", "")
            .str.split(",")
        )  # split hashtags into List[str]
        .name.keep()
    )

    # select columns
    df_input = df_input.select(pl.col(COLS_ALL))

    df_agg = (
        df_input.filter(pl.col(COL_HASHTAGS).is_not_null())
        .select(
            pl.col(COL_TIME),
            pl.col(COL_HASHTAGS),
        )
        .sort(COL_TIME)
        .group_by_dynamic(COL_TIME, every="1h")  # this could be a parameter
        .agg(
            pl.col(COL_HASHTAGS).explode().alias(OUTPUT_COL_HASHTAGS),
            pl.col(COL_HASHTAGS).explode().count().alias(OUTPUT_COL_COUNT),
            pl.col(COL_HASHTAGS)
            .explode()
            .map_elements(
                lambda x: gini(x.to_list()),
                return_dtype=pl.Float32,
                returns_scalar=True,
            )
            .alias(OUTPUT_COL_GINI),
        )
    )

    print("Output preview:")
    print(df_agg.head())

    df_agg.write_parquet(context.output(OUTPUT_GINI).parquet_path)
