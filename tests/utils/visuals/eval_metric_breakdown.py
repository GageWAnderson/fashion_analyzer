import plotly.graph_objects as go
import pandas as pd
from plotly.subplots import make_subplots


def eval_metric_breakdown(df: pd.DataFrame) -> go.Figure:
    # Filter for rows with non-null test_type
    filtered_df = df[df["test_type"].notna()]

    # Melt the dataframe to get metrics in one column
    melted_df = pd.melt(
        filtered_df,
        id_vars=["test_type"],
        value_vars=["overall_metrics", "ragas", "rai"],
        var_name="metric",
        value_name="score",
    )

    eval_metric_breakdown = make_subplots(
        rows=1,
        cols=1,
        subplot_titles=("Evaluation Metric Breakdown",),
        specs=[[{"type": "bar"}]],
    )

    eval_metric_breakdown.add_trace(
        go.Bar(
            x=[f"{row.test_type} - {row.metric}" for _, row in melted_df.iterrows()],
            y=melted_df["score"],
            name="Scores",
        )
    )

    eval_metric_breakdown.update_layout(
        xaxis_title="Test Type - Metric", yaxis_title="Score", xaxis_tickangle=45
    )

    return eval_metric_breakdown
