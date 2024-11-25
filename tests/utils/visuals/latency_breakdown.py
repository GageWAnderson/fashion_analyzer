import plotly.graph_objects as go
import pandas as pd
from plotly.subplots import make_subplots


def latency_breakdown(df: pd.DataFrame) -> go.Figure:
    # Filter for rows with non-null duration
    filtered_df = df[df["duration"].notna()]

    # Define latency buckets
    buckets = [(0, 1), (1, 5), (5, 10), (10, 20), (20, 30)]
    bucket_labels = ["0-1s", "1-5s", "5-10s", "10-20s", "20-30s", "30+s"]

    # Count samples in each bucket
    counts = []
    for i, (low, high) in enumerate(buckets):
        count = len(
            filtered_df[
                (filtered_df["duration"] >= low) & (filtered_df["duration"] < high)
            ]
        )
        counts.append(count)

    # Add 30+ seconds bucket
    counts.append(len(filtered_df[filtered_df["duration"] >= 30]))

    # Create subplot
    latency_dist = make_subplots(
        rows=1,
        cols=1,
        subplot_titles=("Latency Distribution",),
        specs=[[{"type": "bar"}]],
    )

    # Add bar chart trace
    latency_dist.add_trace(go.Bar(x=bucket_labels, y=counts, name="Request Count"))

    # Update layout
    latency_dist.update_layout(
        xaxis_title="Latency Range",
        yaxis_title="Number of Requests",
        showlegend=True,
    )

    return latency_dist
