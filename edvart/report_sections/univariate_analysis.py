"""Univariate analysis package."""
# Standard imports
import warnings
from typing import Any, Callable, Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import nbformat.v4 as nbfv4
import pandas as pd
import seaborn as sns

# Third-party library imports
from IPython.display import HTML, Markdown, display

# Internal library imports
from edvart import utils
from edvart.data_types import DataType, infer_data_type
from edvart.pandas_formatting import add_html_heading, dict_to_html, format_number, subcells_html
from edvart.report_sections.code_string_formatting import code_dedent, get_code
from edvart.report_sections.section_base import Section


class UnivariateAnalysis(Section):
    """Generates univariate analysis section of the report.

    Parameters
    -----------
    df : pd.DataFrame
        Dataframe to be analyzed
    verbosity : int
        The verbosity of the code generated in the exported notebook,
        must be one of [0, 1, 2].

        0
            A single function call generates the entire univariate analysis section.
        1
            Function calls to parameterizable functions are generated for each column separately
            in separate cells.
        2
            Similar to 1, but in addition, function definitions are generated, column
            data type inference and default statistics become customizable.

    columns : List[str], optional
        List of columns for which to do univariate analysis,
        all columns are used by default
    """

    def __init__(self, df: pd.DataFrame, verbosity: int = 0, columns: Optional[List[str]] = None):
        self.df = df
        super().__init__(verbosity, columns)

    @property
    def name(self) -> str:
        return "Univariate Analysis"

    @staticmethod
    def default_descriptive_statistics():
        """
        Return default descriptive statistics.

        Returns
        -------
        dict
            Dictionary with keys as statistics names and values with functions.
        """
        return {
            "Number of unique values": utils.num_unique_values,
            "Sum": utils.sum_,
            "Mean": utils.mean,
            "Mode": utils.mode,
            "Standard deviation": utils.std,
            "Mean absolute deviation": utils.mad,
            "Median absolute deviation": utils.median_absolute_deviation,
            "Coefficient of variation": utils.coefficient_of_variation,
            "Kurtosis": utils.kurtosis,
            "Skewness": utils.skewness,
        }

    @staticmethod
    def default_quantile_statistics():
        """
        Return default quantile statistics.

        Returns
        -------
        dict
            Dictionary with keys as statistics names and values with functions.
        """
        return {
            "Minimum": utils.minimum,
            "Maximum": utils.maximum,
            "Q1": utils.quartile1,
            "Median": utils.median,
            "Q3": utils.quartile3,
            "Range": utils.value_range,
            "IQR": utils.iqr,
        }

    @staticmethod
    def histogram(
        series: pd.Series,
        bins: Optional[int] = None,
        density: bool = False,
        box_plot: bool = True,
        figsize: Tuple[float, float] = (20, 7),
        distplot_kwargs: Optional[Dict[str, Any]] = None,
        boxplot_kwargs: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Visualizes distribution of series with a histogram.

        Parameters
        ----------
        series : pd.Series
            Numerical series.
        bins : int, optional
            Number of bins of the histogram. If None, the number of bins is inferred.
        density : bool (default = False)
            If True, the area of the histogram bars will sum up to 1.
        box_plot : bool (default = True)
            If True, a horizontal box plot will be added above the histogram to visualize quartiles.
        figsize : Tuple[float, float] (default = (20, 7))
            Size of the figure of the visualization.
        distplot_kwargs : Dict[str, Any], optional
            Additional keyword arguments passed to seaborn.distplot
        boxplot_kwargs : Dict[str, Any], optional
            Additional keyword arguments passed to seaborn.boxplot
        """
        if distplot_kwargs is None:
            distplot_kwargs = {}
        if boxplot_kwargs is None:
            boxplot_kwargs = {}

        series = series.dropna()

        if box_plot:
            _fig, (ax_box, ax_hist) = plt.subplots(
                nrows=2,
                sharex=True,
                gridspec_kw={"height_ratios": (0.15, 0.85)},
                figsize=figsize,
            )
            sns.boxplot(x=series, ax=ax_box, **boxplot_kwargs)
            sns.histplot(
                data=series,
                bins=bins if bins is not None else "auto",
                stat="density" if density else "count",
                ax=ax_hist,
                kde=False,
                **distplot_kwargs,
            )
            ax_box.set(xlabel="")
        else:
            plt.figure(figsize=figsize)
            sns.histplot(
                data=series,
                bins=bins if bins is not None else "auto",
                stat="density" if density else "count",
                kde=False,
                **distplot_kwargs,
            )
        plt.show()

    @staticmethod
    def bar_plot(
        series: pd.Series,
        relative_count: bool = False,
        figsize: Tuple[float, float] = (20, 7),
        plotting_threshold: int = 50,
        **bar_plot_args: Dict[str, Any],
    ) -> None:
        """Plots a bar plot visualizing frequencies of series elements.

        Parameters
        ----------
        series : pd.Series
            Categorical series.
        relative_count : bool
            If True, the frequencies will be normalized by the series length.
        figsize : Tuple[float, float]
            Size of the bar plot.
        plotting_threshold : int
            If the number of unique values in the series is greater than this, no plot is created
            instead a warning is issued.
        bar_plot_args : Dict[str, Any]
            Additional kwargs passed to pandas.Series.bar.
        """
        if series.nunique() > plotting_threshold:
            warnings.warn(
                f"Number of unique values is greater than {plotting_threshold},"
                " not plotting bar plot."
            )
        else:
            value_counts = series.value_counts()
            value_counts = value_counts / len(series) if relative_count else value_counts
            value_counts.plot.bar(figsize=figsize, **bar_plot_args)
            plt.show()

    @staticmethod
    def numeric_statistics(
        series: pd.Series,
        descriptive_stats: Optional[Dict[str, Callable]] = None,
        quantile_stats: Optional[Dict[str, Callable]] = None,
        thousand_separator: str = " ",
    ) -> None:
        """Generates tables with statistics for numeric series.

        Parameters
        ----------
        series : pd.Series
            Numeric series.
        descriptive_stats : Dict[str, Callable], optional
            Descriptive statistics computed for the series.
            Dictionary format: {'statistic name': stat_func(pd.Series) -> float}
            If None, UnivariateAnalysis.default_descriptive_statistics is used.
        quantile_stats : Dict[str, Callable], optional
            Quantile statistics computed for the series.
            Dictionary format: {'statistic name': stat_func(pd.Series) -> float}
            If None, UnivariateAnalysis.default_quantile_statistics is used.
        thousand_separator : str
            Thousand separator for numbers in the tables, by default space.
        """
        if descriptive_stats is None:
            descriptive_stats = UnivariateAnalysis.default_descriptive_statistics()
        if quantile_stats is None:
            quantile_stats = UnivariateAnalysis.default_quantile_statistics()

        desc_stats = {
            stat_name: format_number(
                number=stat_func(series), thousand_separator=thousand_separator
            )
            for stat_name, stat_func in descriptive_stats.items()
        }
        quant_stats = {
            stat_name: format_number(
                number=stat_func(series), thousand_separator=thousand_separator
            )
            for stat_name, stat_func in quantile_stats.items()
        }
        # Render statistics tables side by side
        desc_stats_html = add_html_heading(dict_to_html(desc_stats), "Descriptive Statistics", 3)
        quant_stats_html = add_html_heading(dict_to_html(quant_stats), "Quantile Statistics", 3)
        html_table = [[desc_stats_html, quant_stats_html]]
        # Render
        display(HTML(subcells_html(html_table)))

    @staticmethod
    def top_most_frequent(series: pd.Series, n_top: int = 5) -> None:
        """Generates a table with top n most frequent values in series.

        Parameters
        ----------
        series : pd.Series
            Categorical series
        n_top : int
            The number of most frequent values to include in the table.
        """
        frequent_values = dict_to_html(utils.top_frequent_values(series, n_top=n_top))
        frequent_values_html = add_html_heading(frequent_values, "Most frequent values", 3)
        display(HTML(frequent_values_html))

    @staticmethod
    def univariate_analysis(df: pd.DataFrame, columns: Optional[List[str]] = None) -> None:
        """Generates univariate analysis for df.

        Parameters
        ----------
        df : pd.DataFrame
            Dataframe to be analyzed
        columns : List[str], optional
            Subset of df columns to analyze, by default all columns of df are used
        """
        if columns is not None:
            df = df[columns]

        for col in df.columns:
            if df[col].isnull().all():
                display(Markdown(f"## *{col} - NULL*"))
                display(Markdown("The column contains only null values."))
                continue
            data_type_name = infer_data_type(df[col], string_representation=True)
            data_type = infer_data_type(df[col])
            display(Markdown(f"## *{col} - {data_type_name}*"))
            if data_type in (DataType.CATEGORICAL, DataType.BOOLEAN):
                UnivariateAnalysis.top_most_frequent(df[col])
                UnivariateAnalysis.bar_plot(df[col])
            else:
                UnivariateAnalysis.numeric_statistics(df[col])
                UnivariateAnalysis.histogram(df[col])

    def required_imports(self) -> List[str]:
        """Returns a list of imports to be put at the top of a generated notebook.

        Returns
        -------
        List[str]
            List of import strings to be added at the top of the generated notebook.
        """
        if self.verbosity == 0:
            return [
                "from edvart.report_sections.univariate_analysis import UnivariateAnalysis\n"
                "univariate_analysis = UnivariateAnalysis.univariate_analysis"
            ]
        if self.verbosity == 1:
            return [
                "from edvart.report_sections.univariate_analysis import UnivariateAnalysis\n"
                "top_most_frequent = UnivariateAnalysis.top_most_frequent\n"
                "bar_plot = UnivariateAnalysis.bar_plot\n"
                "numeric_statistics = UnivariateAnalysis.numeric_statistics\n"
                "histogram = UnivariateAnalysis.histogram",
                "from edvart import utils",
            ]
        # verbosity 2
        return [
            "from edvart import utils",
            "from IPython.display import display",
            "from IPython.display import HTML",
            "import matplotlib.pyplot as plt",
            "%matplotlib inline",
            "import seaborn as sns",
            "import warnings",
        ]

    def add_cells(self, cells: List[Dict[str, Any]]) -> None:
        """Adds univariate analysis cells to the list of cells.

        Parameters
        ----------
        cells : List[Dict[str, Any]]
            List of generated notebook cells which are represented as dictionaries.
        """
        if self.columns is not None:
            self.df = self.df[self.columns]

        section_header = nbfv4.new_markdown_cell(self.get_title(section_level=1))
        cells.append(section_header)

        if self.verbosity == 2:
            # Add cell with default stats dictionaries
            default_stats_dicts = nbfv4.new_code_cell(
                "# Default statistics dictionaries"
                + 2 * "\n"
                + get_code(UnivariateAnalysis.default_descriptive_statistics)
                + 2 * "\n"
                + get_code(UnivariateAnalysis.default_quantile_statistics)
            )
            cells.append(default_stats_dicts)
            # Add cell with function definitions
            func_defs = nbfv4.new_code_cell(
                get_code(UnivariateAnalysis.top_most_frequent)
                + 2 * "\n"
                + get_code(UnivariateAnalysis.bar_plot)
                + 2 * "\n"
                + (
                    get_code(UnivariateAnalysis.numeric_statistics).replace(
                        "UnivariateAnalysis.", ""
                    )
                )
                + 2 * "\n"
                + get_code(UnivariateAnalysis.histogram)
            )
            cells.append(func_defs)
            # Add cell with dataframe rendering
            frame_rendering = nbfv4.new_code_cell(
                get_code(format_number)
                + 2 * "\n"
                + get_code(dict_to_html)
                + 2 * "\n"
                + get_code(add_html_heading)
                + 2 * "\n"
                + get_code(subcells_html)
            )
            cells.append(frame_rendering)

        if self.verbosity == 0:
            if self.columns is None:
                code = "univariate_analysis(df=df)"
            else:
                code = f"univariate_analysis(df=df, columns={self.columns})"
            code_cell = nbfv4.new_code_cell(code)
            cells.append(code_cell)
        else:
            for col in self.df.columns:
                if self.df[col].isnull().all():
                    display(Markdown(f"## *{col} - NULL*"))
                    display(Markdown("The column contains only null values."))
                    continue
                data_type_name = infer_data_type(self.df[col], string_representation=True)
                data_type = infer_data_type(self.df[col])
                column_header = nbfv4.new_markdown_cell(f"## *{col} - {data_type_name}*")
                cells.append(column_header)
                if data_type in (DataType.CATEGORICAL, DataType.BOOLEAN):
                    code = code_dedent(
                        f"""
                        top_most_frequent(df['{col}'])
                        bar_plot(df['{col}'])"""
                    )
                elif self.verbosity == 1:
                    code = code_dedent(
                        f"""
                            numeric_statistics(df['{col}'])
                            histogram(df['{col}'])"""
                    )
                else:
                    code = code_dedent(
                        f"""
                            numeric_statistics(
                                df['{col}'],
                                descriptive_stats=default_descriptive_statistics(),
                                quantile_stats=default_quantile_statistics()
                            )
                            histogram(df['{col}'])"""
                    )
                code_cell = nbfv4.new_code_cell(code)
                cells.append(code_cell)

    def show(self, df: pd.DataFrame) -> None:
        """Generates univariate analysis cell output in the calling notebook.

        Parameters
        ----------
        df : pd.DataFrame
            Data based on which to generate the cell output
        """
        if self.columns is not None:
            df = df[self.columns]

        display(Markdown(self.get_title(section_level=1)))
        for col in df.columns:
            if df[col].isnull().all():
                display(Markdown(f"## *{col} - NULL*"))
                display(Markdown("The column contains only null values."))
                continue
            data_type_name = infer_data_type(df[col], string_representation=True)
            data_type = infer_data_type(df[col])
            display(Markdown(f"## *{col} - {data_type_name}*"))
            if data_type in (DataType.CATEGORICAL, DataType.BOOLEAN):
                UnivariateAnalysis.top_most_frequent(df[col])
                UnivariateAnalysis.bar_plot(df[col])
            else:
                UnivariateAnalysis.numeric_statistics(df[col])
                UnivariateAnalysis.histogram(df[col])
            display(Markdown("---"))
