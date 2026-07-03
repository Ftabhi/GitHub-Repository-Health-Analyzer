"""Export analytics data from the dashboard."""

import io
import json
from pathlib import Path
from typing import Any, Dict

import pandas as pd


def export_to_csv(metrics: Dict[str, Any], chart_data: Dict[str, pd.DataFrame]) -> bytes:
    """Export metrics and chart data to CSV bytes."""
    buffer = io.StringIO()
    buffer.write("### Metrics\n")
    metrics_df = pd.DataFrame([metrics])
    metrics_df.to_csv(buffer, index=False)
    buffer.write("\n")

    for key, df in chart_data.items():
        buffer.write(f"### {key}\n")
        df.to_csv(buffer, index=False)
        buffer.write("\n")
    return buffer.getvalue().encode("utf-8")


def export_to_json(metrics: Dict[str, Any], chart_data: Dict[str, pd.DataFrame]) -> bytes:
    """Export metrics and chart data to JSON bytes."""
    payload = {
        "metrics": metrics,
        "chart_data": {key: df.to_dict(orient="records") for key, df in chart_data.items()},
    }
    return json.dumps(payload, indent=2).encode("utf-8")


def export_to_pdf(metrics: Dict[str, Any], chart_data: Dict[str, pd.DataFrame], file_name: str) -> bytes:
    """Return simple PDF bytes for analytics export."""
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(40, 740, "Repository Analytics Export")
    pdf.setFont("Helvetica", 10)
    y = 720
    pdf.drawString(40, y, f"Metrics Summary:")
    y -= 20
    for label, value in metrics.items():
        pdf.drawString(50, y, f"{label}: {value}")
        y -= 14
        if y < 100:
            pdf.showPage()
            y = 740
    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return buffer.getvalue()
