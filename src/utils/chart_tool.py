"""圖表渲染工具。

此模組提供用於生成各種類型圖表並將其轉換為 base64 編碼 PNG 圖片的實用類別。
設計用於無頭環境，使用 Matplotlib 函式庫進行圖表渲染。

類別:
- ChartTool: 根據輸入的數值與標籤生成圖表（圓餅圖、甜甜圈圖、水平長條圖、垂直長條圖或折線圖），
    並以 base64 編碼的 PNG 圖片格式返回圖表。
"""

from typing import Literal
import io
import base64
import matplotlib
from matplotlib import font_manager
from src.core.logger_config import get_logger

matplotlib.use("Agg")  # Use Agg backend for headless environments
import matplotlib.pyplot as plt

logger = get_logger(__name__)


class ChartTool:
    ChartType = Literal["pie", "donut", "horizontal_bar", "vertical_bar", "line"]

    _CHINESE_FONT_CANDIDATES = (
        "Microsoft JhengHei",
        "PingFang TC",
        "Noto Sans TC",
        "Heiti TC",
        "Arial Unicode MS",
    )

    _font_configured = False

    @classmethod
    def _configure_chinese_font(cls) -> None:
        """優先選用可支援繁體中文的字型。"""
        available_fonts = {font.name for font in font_manager.fontManager.ttflist}
        default_sans = list(matplotlib.rcParams["font.sans-serif"])
        matplotlib.rcParams["font.family"] = "sans-serif"

        for candidate in cls._CHINESE_FONT_CANDIDATES:
            if candidate in available_fonts:
                updated_fonts = [candidate] + [
                    font for font in default_sans if font != candidate
                ]
                matplotlib.rcParams["font.sans-serif"] = updated_fonts
                return

        if default_sans:
            matplotlib.rcParams["font.sans-serif"] = default_sans

    @classmethod
    def _ensure_font_configured(cls) -> None:
        if cls._font_configured:
            return
        cls._configure_chinese_font()
        cls._font_configured = True

    @staticmethod
    def _truncate_label(label: str, max_length: int = 15) -> str:
        if len(label) > max_length:
            return label[: max_length - 3] + "..."
        return label

    @classmethod
    def chart_to_base64(
        cls,
        values: list[float] | str,
        labels: list[str] | str,
        chart_type: "ChartTool.ChartType",
    ) -> str:
        """根據 values 與 labels 生成圖表，並回傳 PNG base64 data URI。"""

        cls._ensure_font_configured()

        # 處理 labels
        try:
            if isinstance(labels, str):
                labs = [label.strip() for label in labels.split(",")]
            else:
                labs = [str(label).strip() for label in labels]
        except Exception as e:
            raise ValueError(f"無法處理 labels 參數: {e}")

        # 處理 values
        try:
            if isinstance(values, str):
                vals = [float(val.strip()) for val in values.split(",")]
            else:
                vals = [float(val) for val in values]
        except (ValueError, TypeError) as e:
            raise ValueError(f"無法將數值轉換為浮點數: {e}")

        if len(vals) != len(labs):
            raise ValueError("labels 與 values 長度不一致")
        n = len(labs)

        # Generate distinct colors using tab20 colormap
        cmap = plt.cm.get_cmap("tab20")
        colors = [cmap(i / max(1, n - 1)) for i in range(n)]

        buf = io.BytesIO()
        fig = None
        try:
            if chart_type == "pie":
                fig = plt.figure(figsize=(6, 6))
                plt.pie(
                    vals,
                    labels=labs,
                    autopct="%1.1f%%",
                    startangle=90,
                    colors=colors,
                )
                plt.axis("equal")
                fig.savefig(buf, format="png", bbox_inches="tight")
            elif chart_type == "donut":
                fig = plt.figure(figsize=(6, 6))
                plt.pie(
                    vals,
                    labels=labs,
                    autopct="%1.1f%%",
                    startangle=90,
                    colors=colors,
                )
                centre_circle = plt.Circle((0, 0), 0.70, fc="white")
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
                ax.set_xticklabels(
                    [cls._truncate_label(lab) for lab in labs],
                    rotation=45,
                    ha="right",
                )
                ax.set_xlabel("Category")
                ax.set_ylabel("Value")
                ax.grid(True, axis="y", linestyle="--", alpha=0.3)
                fig.tight_layout()
                fig.savefig(buf, format="png", bbox_inches="tight")
            elif chart_type == "line":
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.plot(
                    vals,
                    marker="o",
                    linewidth=2.5,
                    markersize=8,
                    color=colors[0],
                )
                ax.set_xticks(range(n))
                ax.set_xticklabels(
                    [cls._truncate_label(lab) for lab in labs],
                    rotation=45,
                    ha="right",
                )
                ax.set_xlabel("Category")
                ax.set_ylabel("Value")
                ax.grid(True, linestyle="--", alpha=0.3)
                fig.tight_layout()
                fig.savefig(buf, format="png", bbox_inches="tight")
            else:
                raise ValueError(f"Unsupported chart_type: {chart_type}")
        finally:
            if fig is not None:
                plt.close(fig)

        buf.seek(0)
        encoded = base64.b64encode(buf.read()).decode("utf-8")
        return f"data:image/png;base64,{encoded}"
