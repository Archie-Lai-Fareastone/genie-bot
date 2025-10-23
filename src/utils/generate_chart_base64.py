from typing import Iterable, Literal
import io
import base64

import matplotlib
matplotlib.use("Agg")   # Use Agg backend for headless environments
import matplotlib.pyplot as plt


ChartType = Literal["pie", "donut", "horizontal_bar", "vertical_bar", "line"]


def _truncate_label(label: str, max_length: int = 15) -> str:
    """Truncate label if it exceeds max_length, adding ellipsis.
    
    Args:
        label: The label text to truncate.
        max_length: Maximum length before truncation (default: 15).
    
    Returns:
        Truncated label with '...' if necessary.
    """
    if len(label) > max_length:
        return label[:max_length - 3] + "..."
    return label


def chart_to_base64(
    values: Iterable[float],
    labels: Iterable[str],
    chart_type: ChartType = "pie"
) -> str:
    """Render a chart from values and labels and return a PNG base64 data URI.

    Args:
        values: Numerical values for the chart.
        labels: Labels corresponding to each value.
        chart_type: Type of chart to generate. Options: "pie", "donut", "horizontal_bar", "vertical_bar", "line".

    Returns:
        A data URI string (data:image/png;base64,...) containing the PNG image.
    
    Raises:
        ValueError: If an unsupported chart_type is provided.
    """
    labs = [str(label) for label in labels]
    # 確保將數值轉換為 float，避免字串導致的問題
    try:
        vals = [float(val) for val in values]
    except (ValueError, TypeError) as e:
        raise ValueError(f"無法將數值轉換為浮點數: {e}")
    
    n = len(labs)
    
    # Generate distinct colors using tab20 colormap
    cmap = plt.cm.get_cmap("tab20")
    colors = [cmap(i / max(1, n - 1)) for i in range(n)]
    
    buf = io.BytesIO()
    try:
        if chart_type == "pie":
            fig = plt.figure(figsize=(6, 6))
            plt.pie(vals, labels=labs, autopct="%1.1f%%", startangle=90, colors=colors)
            plt.axis("equal")
            fig.savefig(buf, format="png", bbox_inches="tight")
        elif chart_type == "donut":
            fig = plt.figure(figsize=(6, 6))
            wedges, texts, autotexts = plt.pie(vals, labels=labs, autopct="%1.1f%%", 
                                               startangle=90, colors=colors)
            # Create donut by drawing a white circle in the center
            centre_circle = plt.Circle((0, 0), 0.70, fc='white')
            fig.gca().add_artist(centre_circle)
            plt.axis("equal")
            fig.savefig(buf, format="png", bbox_inches="tight")
        elif chart_type == "horizontal_bar":
            fig, ax = plt.subplots(figsize=(8, max(2, n * 0.5)))
            ax.barh(labs, vals, color=colors)
            ax.set_xlabel("Value")
            ax.set_ylabel("Category")
            fig.tight_layout()
            fig.savefig(buf, format="png", bbox_inches="tight")
        elif chart_type == "vertical_bar":
            fig, ax = plt.subplots(figsize=(max(6, n * 0.6), 6))
            ax.bar(range(n), vals, color=colors)
            ax.set_xticks(range(n))
            ax.set_xticklabels([_truncate_label(lab) for lab in labs], rotation=45, ha='right')
            ax.set_xlabel("Category")
            ax.set_ylabel("Value")
            # 加入格線以便更容易讀取數值
            ax.grid(True, axis='y', linestyle='--', alpha=0.3)
            fig.tight_layout()
            fig.savefig(buf, format="png", bbox_inches="tight")
        elif chart_type == "line":
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(vals, marker='o', linewidth=2.5, markersize=8, color=colors[0])
            ax.set_xticks(range(n))
            ax.set_xticklabels([_truncate_label(lab) for lab in labs], rotation=45, ha='right')
            ax.set_xlabel("Category")
            ax.set_ylabel("Value")
            ax.grid(True, linestyle='--', alpha=0.3)
            fig.tight_layout()
            fig.savefig(buf, format="png", bbox_inches="tight")
        else:
            raise ValueError(f"Unsupported chart_type: {chart_type}")
    finally:
        plt.close(fig)
    
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode("utf-8")
    return f"data:image/png;base64,{encoded}"


