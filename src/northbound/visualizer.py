#!/usr/bin/env python3
"""
Visualization tools for trading strategy performance.
"""

import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from typing import List, Optional


class PerformanceVisualizer:
    """Creates visualizations for strategy performance."""

    def __init__(self):
        self.data_cache = {}

    def load_csv_data(self, csv_path: str) -> pd.DataFrame:
        """Load and cache CSV data."""
        if csv_path not in self.data_cache:
            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path)
                df["Date"] = pd.to_datetime(df["Date"])
                self.data_cache[csv_path] = df
            else:
                raise FileNotFoundError(f"CSV file not found: {csv_path}")

        return self.data_cache[csv_path].copy()

    def normalize_prices(
        self, df: pd.DataFrame, start_value: float = 100.0
    ) -> pd.Series:
        """Normalize price series to start at a given value."""
        if df.empty or "Close" not in df.columns:
            return pd.Series()

        first_price = df["Close"].iloc[0]
        if first_price == 0:
            return pd.Series([start_value] * len(df), index=df.index)

        return (df["Close"] / first_price) * start_value

    def plot_portfolio_performance(
        self,
        csv_paths: List[str],
        labels: Optional[List[str]] = None,
        start_date: str = None,
        end_date: str = None,
        normalize: bool = True,
        interactive: bool = True,
        save_path: str = None,
    ) -> None:
        """
        Plot portfolio performance over time.

        Args:
            csv_paths: List of CSV file paths to plot
            labels: Labels for each series (defaults to filenames)
            start_date: Start date filter (YYYY-MM-DD)
            end_date: End date filter (YYYY-MM-DD)
            normalize: Whether to normalize all series to same starting value
            interactive: Whether to create interactive plotly chart
        """
        if labels is None:
            labels = []
            for path in csv_paths:
                df = self.load_csv_data(path)
                if "Strategy_Name" in df.columns and not df.empty:
                    labels.append(df["Strategy_Name"].iloc[0])
                else:
                    labels.append(os.path.basename(path).replace(".csv", ""))

        if len(csv_paths) != len(labels):
            raise ValueError("Number of CSV paths must match number of labels")

        data_frames = []
        for path in csv_paths:
            df = self.load_csv_data(path)

            # Filter date range
            if start_date:
                df = df[df["Date"] >= start_date]
            if end_date:
                df = df[df["Date"] <= end_date]

            data_frames.append(df)

        # Create plot
        if interactive:
            self._create_interactive_plot(data_frames, labels, normalize, save_path)
        else:
            self._create_static_plot(data_frames, labels, normalize)

    def _create_interactive_plot(
        self,
        data_frames: List[pd.DataFrame],
        labels: List[str],
        normalize: bool,
        save_path: str = None,
    ) -> None:
        """Create interactive plotly chart."""
        fig = go.Figure()

        for i, (df, label) in enumerate(zip(data_frames, labels)):
            if df.empty:
                continue

            x_data = df["Date"]

            if "Portfolio_Value" in df.columns:
                # Strategy results CSV
                y_data = df["Portfolio_Value"]
                title = "Portfolio Value Over Time"
                y_label = "Portfolio Value ($)"
            elif "Close" in df.columns:
                # Price data CSV
                if normalize:
                    y_data = self.normalize_prices(df, 100.0)
                    title = "Normalized Performance (Starting at $100)"
                    y_label = "Normalized Value"
                else:
                    y_data = df["Close"]
                    title = "Price Over Time"
                    y_label = "Price ($)"
            else:
                continue

            fig.add_trace(
                go.Scatter(
                    x=x_data,
                    y=y_data,
                    mode="lines",
                    name=label,
                    hovertemplate=f"{label}<br>Date: %{{x}}<br>Value: %{{y:.2f}}<extra></extra>",
                )
            )

        fig.update_layout(
            title=title,
            xaxis_title="Date",
            yaxis_title=y_label,
            hovermode="x unified",
            template="plotly_white",
        )

        # Print performance summary
        print(f"\n{title}")
        print("=" * 60)
        for i, (df, label) in enumerate(zip(data_frames, labels)):
            if df.empty:
                continue

            if "Portfolio_Value" in df.columns:
                final_value = df["Portfolio_Value"].iloc[-1]
                initial_value = df["Portfolio_Value"].iloc[0]
                total_return = (final_value - initial_value) / initial_value * 100
                print(f"{label}: ${final_value:,.2f} ({total_return:+.2f}%)")
            elif "Close" in df.columns:
                if normalize:
                    normalized = self.normalize_prices(df, 100.0)
                    final_value = normalized.iloc[-1]
                    total_return = (final_value - 100.0) / 100.0 * 100
                    print(f"{label}: {final_value:.2f} ({total_return:+.2f}%)")
                else:
                    final_price = df["Close"].iloc[-1]
                    initial_price = df["Close"].iloc[0]
                    total_return = (final_price - initial_price) / initial_price * 100
                    print(f"{label}: ${final_price:.2f} ({total_return:+.2f}%)")

        # Save as HTML file
        if save_path:
            fig.write_html(save_path)
            print(f"\nChart saved to: {save_path}")
        else:
            # Try to show the plot, but save as HTML if it fails
            try:
                fig.show()
            except Exception as e:
                print(f"Could not display interactive plot: {e}")
                temp_path = f"visualizations/performance_chart_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.html"
                fig.write_html(temp_path)
                print(f"Chart saved to: {temp_path}")

    def _create_static_plot(
        self, data_frames: List[pd.DataFrame], labels: List[str], normalize: bool
    ) -> None:
        """Create static matplotlib chart."""
        plt.figure(figsize=(12, 8))

        for i, (df, label) in enumerate(zip(data_frames, labels)):
            if df.empty:
                continue

            if "Portfolio_Value" in df.columns:
                plt.plot(df["Date"], df["Portfolio_Value"], label=label, linewidth=2)
                title = "Portfolio Value Over Time"
                ylabel = "Portfolio Value ($)"
            elif "Close" in df.columns:
                if normalize:
                    normalized = self.normalize_prices(df, 100.0)
                    plt.plot(df["Date"], normalized, label=label, linewidth=2)
                    title = "Normalized Performance (Starting at $100)"
                    ylabel = "Normalized Value"
                else:
                    plt.plot(df["Date"], df["Close"], label=label, linewidth=2)
                    title = "Price Over Time"
                    ylabel = "Price ($)"

        plt.title(title, fontsize=16)
        plt.xlabel("Date", fontsize=12)
        plt.ylabel(ylabel, fontsize=12)
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

    def compare_strategies(
        self,
        strategy_csvs: List[str],
        benchmark_csv: str = None,
        start_date: str = None,
        end_date: str = None,
        save_path: str = None,
    ) -> None:
        """
        Compare multiple strategies against each other and/or a benchmark.

        Args:
            strategy_csvs: List of strategy result CSV paths
            benchmark_csv: Optional benchmark price data CSV
            start_date: Start date filter
            end_date: End date filter
            save_path: Path to save HTML file (defaults to subfolder)
        """
        csv_paths = strategy_csvs.copy()

        # Get labels, using Strategy_Name if available
        labels = []
        for path in strategy_csvs:
            df = self.load_csv_data(path)
            if "Strategy_Name" in df.columns and not df.empty:
                labels.append(df["Strategy_Name"].iloc[0])
            else:
                labels.append(os.path.basename(path).replace(".csv", ""))

        if benchmark_csv:
            csv_paths.append(benchmark_csv)
            # For benchmark, use Strategy_Name if available, otherwise filename
            df = self.load_csv_data(benchmark_csv)
            if "Strategy_Name" in df.columns and not df.empty:
                labels.append(df["Strategy_Name"].iloc[0])
            else:
                labels.append(os.path.basename(benchmark_csv).replace(".csv", ""))

        # If no save_path provided, save in the same folder as the first strategy
        if save_path is None and strategy_csvs:
            base_dir = os.path.dirname(strategy_csvs[0])
            save_path = os.path.join(base_dir, "strategy_comparison.html")

        self.plot_portfolio_performance(
            csv_paths,
            labels,
            start_date,
            end_date,
            normalize=True,
            interactive=True,
            save_path=save_path,
        )

    def plot_allocation_over_time(
        self, strategy_csv: str, start_date: str = None, end_date: str = None
    ) -> None:
        """
        Plot allocation percentages over time for a strategy.

        Args:
            strategy_csv: Path to strategy results CSV
            start_date: Start date filter
            end_date: End date filter
        """
        df = self.load_csv_data(strategy_csv)

        # Filter date range
        if start_date:
            df = df[df["Date"] >= start_date]
        if end_date:
            df = df[df["Date"] <= end_date]

        if df.empty or "Allocation" not in df.columns:
            print("No allocation data found")
            return

        # Parse allocation JSON
        allocations = []
        dates = []
        assets = set()

        for _, row in df.iterrows():
            try:
                alloc = eval(row["Allocation"])  # Use eval for JSON stored as string
                if isinstance(alloc, dict):
                    allocations.append(alloc)
                    dates.append(row["Date"])
                    assets.update(alloc.keys())
            except:
                continue

        if not allocations:
            print("No valid allocation data found")
            return

        # Create stacked area chart
        assets = sorted(list(assets))
        alloc_matrix = []

        for alloc in allocations:
            row = [alloc.get(asset, 0) for asset in assets]
            alloc_matrix.append(row)

        # Create plotly figure
        fig = go.Figure()

        for i, asset in enumerate(assets):
            fig.add_trace(
                go.Scatter(
                    x=dates,
                    y=[row[i] for row in alloc_matrix],
                    mode="lines",
                    stackgroup="one",
                    name=asset,
                    hovertemplate=f"{asset}: %{{y:.1f}}%<extra></extra>",
                )
            )

        fig.update_layout(
            title="Portfolio Allocation Over Time",
            xaxis_title="Date",
            yaxis_title="Allocation (%)",
            hovermode="x unified",
            template="plotly_white",
        )

        fig.show()


def create_performance_chart(
    csv_paths: List[str],
    labels: Optional[List[str]] = None,
    start_date: str = None,
    end_date: str = None,
    normalize: bool = True,
) -> None:
    """
    Convenience function to create performance charts.

    Args:
        csv_paths: List of CSV file paths
        labels: Labels for each series
        start_date: Start date filter
        end_date: End date filter
        normalize: Whether to normalize values
    """
    visualizer = PerformanceVisualizer()
    visualizer.plot_portfolio_performance(
        csv_paths, labels, start_date, end_date, normalize
    )
