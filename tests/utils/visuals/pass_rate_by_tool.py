import plotly.graph_objects as go
import pandas as pd
from plotly.subplots import make_subplots


def pass_rate_by_tool(df: pd.DataFrame) -> go.Figure:
    test_types = df["test_type"].unique()
    num_types = len(test_types)
    
    fig = make_subplots(
        rows=num_types, 
        cols=1,
        subplot_titles=[f"{test_type} Pass Rate" for test_type in test_types]
    )
    
    for i, test_type in enumerate(test_types, start=1):
        type_df = df[df["test_type"] == test_type]
        pass_rate = len(type_df[type_df["passed"] == True]) / len(type_df) * 100
        
        fig.add_trace(
            go.Bar(
                x=[test_type],
                y=[pass_rate],
                name=test_type
            ),
            row=i,
            col=1
        )
        
        fig.update_yaxes(title_text="Pass Rate (%)", row=i, col=1)
        
    fig.update_layout(
        height=300 * num_types,
        showlegend=False,
        title_text="Pass Rates by Test Type"
    )
    
    return fig
