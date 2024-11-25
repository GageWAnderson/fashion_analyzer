import pandas as pd
from pathlib import Path

from plotly.offline import plot

from tests.utils.visuals.overall_pass_rate import overall_pass_rate
from tests.utils.visuals.pass_rate_by_tool import pass_rate_by_tool
from tests.utils.visuals.eval_metric_breakdown import eval_metric_breakdown
from tests.utils.visuals.latency_breakdown import latency_breakdown


def create_test_report(df: pd.DataFrame, test_outputs_dir: Path, run_id: str) -> None:
    with open(str(test_outputs_dir / f"test_report_{run_id}.html"), "w") as f:
        f.write("<html><head><title>Test Report</title></head><body>")
        f.write(
            plot(
                overall_pass_rate(df),
                output_type="div",
                include_plotlyjs="cdn",
                auto_play=False,
            )
        )
        f.write(
            plot(
                pass_rate_by_tool(df),
                output_type="div",
                include_plotlyjs="cdn",
                auto_play=False,
            )
        )
        f.write(
            plot(
                eval_metric_breakdown(df),
                output_type="div",
                include_plotlyjs="cdn",
                auto_play=False,
            )
        )
        f.write(
            plot(
                latency_breakdown(df),
                output_type="div",
                include_plotlyjs="cdn",
                auto_play=False,
            )
        )
        f.write("</body></html>")
