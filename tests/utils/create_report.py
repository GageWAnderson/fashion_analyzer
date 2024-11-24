import pandas as pd
from pathlib import Path

from plotly.offline import plot

from tests.utils.visuals.overall_pass_rate import overall_pass_rate


def create_test_report(df: pd.DataFrame, test_outputs_dir: Path) -> None:
    with open(str(test_outputs_dir / "test_report.html"), "w") as f:
        f.write("<html><head><title>Test Report</title></head><body>")
        f.write(
            plot(
                overall_pass_rate(df),
                output_type="div",
                include_plotlyjs="cdn",
                auto_play=False,
            )
        )
        # f.write(
        #     plot(
        #         router_pass_rate(df),
        #         output_type="div",
        #         include_plotlyjs="cdn",
        #         auto_play=False,
        #     )
        # )
        # f.write(
        #     plot(
        #         pass_rate_by_tool(df),
        #         output_type="div",
        #         include_plotlyjs="cdn",
        #         auto_play=False,
        #     )
        # )
        # f.write(
        #     plot(
        #         pass_rate_by_tool(df),
        #         output_type="div",
        #         include_plotlyjs="cdn",
        #         auto_play=False,
        #     )
        # )
        # f.write(
        #     plot(
        #         eval_metric_breakdown(df),
        #         output_type="div",
        #         include_plotlyjs="cdn",
        #         auto_play=False,
        #     )
        # )
        # f.write(
        #     plot(
        #         latency_breakdown(df),
        #         output_type="div",
        #         include_plotlyjs="cdn",
        #         auto_play=False,
        #     )
        # )
        f.write("</body></html>")