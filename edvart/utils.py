"""Utils package."""

from typing import Any, Dict, Iterable, List, Literal, Optional, Tuple, Union

import pandas as pd
import seaborn as sns
import statsmodels.api as sm

from edvart.data_types import is_numeric


def is_categorical(series: pd.Series, nunique_max: int = 20) -> bool:
    """
    A heuristic of whether a series is categorical or numerical.

    Parameters
    ----------
    series: pd.Series
        Input series
    nunique_max: int (default = 20)
        Maximum number of unique values for a numeric series to be regarded as categorical.
        No limit on number of unique values if set to a negative number.

    Returns
    -------
    bool
        True if series contains categorical values, otherwise False
    """
    return (
        (nunique_max < 0 or series.nunique() <= nunique_max) or not is_numeric(series)
    ) and not pd.core.dtypes.common.is_datetime_or_timedelta_dtype(series)


def top_frequent_values(series: pd.Series, n_top: int = 10) -> Dict[Any, float]:
    """
    Counts top n most frequent values in series along with other value counts and NULL value counts.

    Parameters
    ---
    series: pd.Series
        Input series of data for which frequencies will be calculated
    n_top: int
        Number of values for which actual frequencies will be counted, other values will be grouped
        into 'Other' category

    Returns
    -------
    result_dict: Dict
        Dictionary with the mapping {'value': 'frequency (relative frequency)'}
    """
    # Calculate frequencies
    counts = series.value_counts()
    nan_count = series.isna().sum()
    result_dict = {
        **(counts[:n_top].to_dict()),
        "Other values count": counts[n_top:].sum(),
        "Null": nan_count,
    }

    # Add relative frequencies
    for key, _value in result_dict.items():
        result_dict[key] = f"{result_dict[key]:,} ({100 * result_dict[key] / len(series):.02f} %)"

    return result_dict


def reindex_to_datetime(
    df: pd.DataFrame,
    datetime_column: str,
    keep_index: Optional[str] = None,
    unit: str = "ns",
    origin: Union[str, pd.Timestamp] = "unix",
    sort: bool = True,
) -> pd.DataFrame:
    """Reindex a given DataFrame to be indexed by a pd.DateTimeIndex.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame to reindex.
    datetime_column : str
        Which column containing datetimes to index by.
    keep_index : str, optional
        Name of column to store the original index. The original index will be discarded
        by default.
    unit : str (default = "ns")
        Numeric values would be parsed as number of units from origin.
    origin : Union[str, pd.Timestamp] (default = "unix")
        Define the reference date. Numeric values would be parsed as number of units
        (defined by unit) since this reference date. By default unix epoch 1970-01-01.
    sort : bool (default = True)
        Whether to sort according to the index.

    Returns
    -------
    pd.DataFrame
        Reindexed df.
    """
    df = df.copy()
    new_index = pd.to_datetime(
        df[datetime_column], unit=unit, origin=origin, infer_datetime_format=True
    )
    if keep_index is not None:
        df[keep_index] = df.index
    df = df.drop(datetime_column, axis="columns")
    df.index = pd.DatetimeIndex(new_index)
    if sort:
        df = df.sort_index()

    return df


def reindex_to_period(
    df: pd.DataFrame,
    period_column: str,
    freq: Optional[str],
    keep_index: Optional[str] = None,
    sort: bool = True,
) -> pd.DataFrame:
    """Reindex a given DataFrame to be indexed by a pd.PeriodIndex.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame to reindex.
    period_column : str
        Which column containing periods to index by.
    freq : Union[str, pd.Offset]
        One of pandas’ offset strings or an Offset object. Will be inferred by default.
    keep_index : str, optional
        Name of column to store the original index. The original index will be discarded
        by default.
    sort : bool (default = True)
        Whether to sort according to the index.

    Returns
    -------
    pd.DataFrame
        Reindexed df.
    """
    df = df.copy()
    new_index = df[period_column].to_period(freq=freq)
    if keep_index is not None:
        df[keep_index] = df.index
    df = df.drop(period_column, axis="columns")
    df.index = pd.PeriodIndex(new_index)
    if sort:
        df = df.sort_index()

    return df


def discrete_colorscale(n, saturation=0.5, lightness=0.5) -> Iterable[Tuple[float, str]]:
    """
    Generate a colorscale of n discrete colors.

    Colours are equally spaced around the complete HSL wheel with constant saturation and lightness.

    Returns
    -------
    Iterable[Tuple[float, str]]
        An iterable of 2n tuples, where each tuple contains a value between 0 and 1
        (the values are equally and each value appears twice) and an HSL string containing
        an HSL color string with hue corresponding to the value.
    """
    for i in range(n):
        color = f"hsl({(i / n) * 360 :.2f}, {saturation * 100 :.2f}%, {lightness * 100 :.2f}%)"
        yield (i / n, color)
        yield ((i + 1) / n, color)


#######################
# Statistic functions #
#######################


def num_unique_values(series: pd.Series) -> int:
    """
    Return number of unique values.

    Parameters
    ----------
    series: pd.Series
        Series on which the stat should be calculated.

    Returns
    -------
    int
    """
    return series.nunique()


def median_absolute_deviation(series: pd.Series) -> float:
    """
    Return median absolute deviation.

    Parameters
    ----------
    series: pd.Series
        Series on which the stat should be calculated.

    Returns
    -------
    float
    """
    return median((series - series.mean()).abs())


def coefficient_of_variation(series: pd.Series) -> float:
    """
    Return coefficient of variation.

    Parameters
    ----------
    series: pd.Series
        Series on which the stat should be calculated.

    Returns
    -------
    float
    """
    return series.std() / series.mean()


def minimum(series: pd.Series) -> float:
    """
    Return minimum.

    Parameters
    ----------
    series: pd.Series
        Series on which the stat should be calculated.

    Returns
    -------
    float
    """
    return series.min()


def maximum(series: pd.Series) -> float:
    """
    Return maximum.

    Parameters
    ----------
    series: pd.Series
        Series on which the stat should be calculated.

    Returns
    -------
    float
    """
    return series.max()


def quartile1(series: pd.Series) -> float:
    """
    Return first quartile.

    Parameters
    ----------
    series: pd.Series
        Series on which the stat should be calculated.

    Returns
    -------
    float
    """
    return series.quantile(0.25)


def quartile3(series: pd.Series) -> float:
    """
    Return third quartile.

    Parameters
    ----------
    series: pd.Series
        Series on which the stat should be calculated.

    Returns
    -------
    float
    """
    return series.quantile(0.75)


def mean(series: pd.Series) -> float:
    """
    Return mean.

    Parameters
    ----------
    series: pd.Series
        Series on which the stat should be calculated.

    Returns
    -------
    float
    """
    return series.mean()


def median(series: pd.Series) -> float:
    """
    Return median.

    Parameters
    ----------
    series: pd.Series
        Series on which the stat should be calculated.

    Returns
    -------
    float
    """
    if series.isnull().all():
        return float("nan")
    return series.median()


def iqr(series: pd.Series) -> float:
    """
    Return inter quartile range.

    Parameters
    ----------
    series: pd.Series
        Series on which the stat should be calculated.

    Returns
    -------
    float
    """
    return series.quantile(0.75) - series.quantile(0.25)


def value_range(series: pd.Series) -> float:
    """
    Return value range.

    Parameters
    ----------
    series: pd.Series
        Series on which the stat should be calculated.

    Returns
    -------
    float
    """
    return series.max() - series.min()


def mode(series: pd.Series) -> float:
    """
    Return mode.

    Parameters
    ----------
    series: pd.Series
        Series on which the stat should be calculated.

    Returns
    -------
    float
        The most frequent value. `float('nan')` if the series contains only null values.
    """
    most_frequent = series.mode(dropna=True)
    if len(most_frequent) == 0:
        return float("nan")
    return most_frequent[0]


def std(series: pd.Series) -> float:
    """
    Return standard deviation.

    Parameters
    ----------
    series: pd.Series
        Series on which the stat should be calculated.

    Returns
    -------
    float
    """
    return series.std()


def mad(series: pd.Series) -> Any:
    """
    Return mean absolute deviation.

    Parameters
    ----------
    series: pd.Series
        Series on which the stat should be calculated.

    Returns
    -------
    float
    """
    return (series - series.mean()).abs().mean()


def kurtosis(series: pd.Series) -> Any:
    """
    Return kurtosis.

    Parameters
    ----------
    series: pd.Series
        Series on which the stat should be calculated.

    Returns
    -------
    float
    """
    return series.kurtosis()


def skewness(series: pd.Series) -> Any:
    """
    Return skewness.

    Parameters
    ----------
    series: pd.Series
        Series on which the stat should be calculated.

    Returns
    -------
    float
    """
    return series.skew()


def sum_(series: pd.Series) -> float:
    """
    Return sum.

    Parameters
    ----------
    series: pd.Series
        Series on which the stat should be calculated.

    Returns
    -------
    float
    """
    return series.sum(min_count=1)


def pearson(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return pearson correlation coefficient.

    Parameters
    ----------
    df: pd.DataFrame
        DataFrame on which the stat should be calculated.

    Returns
    -------
    pd.DataFrame
    """
    return _corr(df, "pearson")


def spearman(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return spearman correlation coefficient.

    Parameters
    ----------
    df: pd.DataFrame
        DataFrame on which the stat should be calculated.

    Returns
    -------
    pd.DataFrame
    """
    return _corr(df, "spearman")


def kendall(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return kendall correlation coefficient.

    Parameters
    ----------
    df: pd.DataFrame
        DataFrame on which the stat should be calculated.

    Returns
    -------
    pd.DataFrame
    """
    return _corr(df, "kendall")


def _corr(df: pd.DataFrame, method: Literal["pearson", "kendall", "spearman"]) -> pd.DataFrame:
    return df.corr(method=method, numeric_only=True)


def pair_plot(
    df: pd.DataFrame,
    columns_x: Optional[List[str]] = None,
    columns_y: Optional[List[str]] = None,
    color_col: Optional[str] = None,
) -> None:
    """
    Plot a pairplot.

    Parameters
    ----------
    df: pd.DataFrame
        DataFrame used for pairplot
    columns_x: List[str], optional
        List of columns to plot on the x-axis.
    columns_y : List[str], optional
        List of columns to plot on the y-axis.
    color_col : str, optional
        Name of columns according to which to color points in the pairplot and univariate
        distribution plots on the diagonals.
    """
    sns.pairplot(df, x_vars=columns_x, y_vars=columns_y, hue=color_col)


def contingency_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return contingency table.

    Parameters
    ----------
    df: pd.DataFrame

    Returns
    -------
    pd.DataFrame
    """
    table = sm.stats.Table.from_data(df)
    return table.table_orig.astype(int)
