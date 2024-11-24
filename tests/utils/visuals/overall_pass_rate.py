import plotly.graph_objects as go
import pandas as pd
from plotly.subplots import make_subplots


def overall_pass_rate(df: pd.DataFrame) -> go.Figure:
    pie_chart = make_subplots(rows=1, cols=1, specs=[[{"type": "pie"}]])
    pie_chart.update_layout(title="Overall Pass Rate")
    values = [len(df[df["passed"] == True]), len(df[df["passed"] == False])]
    pie_chart.add_trace(go.Pie(labels=["Pass", "Fail"], values=values), row=1, col=1)
    return pie_chart
