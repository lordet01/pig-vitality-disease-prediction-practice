"""
pipeline_summary_by_pen.csv 시각화

돈방별 요약 통계에 맞는 여러 형태의 plot을 그려 results/figures/ 에 저장한다.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np
import pandas as pd
import seaborn as sns

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CSV = ROOT / "results" / "pipeline_summary_by_pen.csv"
DEFAULT_OUTDIR = ROOT / "results" / "figures"

# macOS/Windows/Linux에서 흔히 있는 한글 폰트 후보
_KOREAN_FONT_CANDIDATES = [
    "Apple SD Gothic Neo",
    "AppleGothic",
    "NanumGothic",
    "Malgun Gothic",
    "Noto Sans CJK KR",
]


def _configure_korean_font() -> str | None:
    available = {f.name for f in font_manager.fontManager.ttflist}
    for name in _KOREAN_FONT_CANDIDATES:
        if name in available:
            plt.rcParams["font.family"] = name
            plt.rcParams["axes.unicode_minus"] = False
            return name
    plt.rcParams["axes.unicode_minus"] = False
    return None

METRIC_COLS = [
    "mean_vitality",
    "mean_activity",
    "mean_cough",
    "mean_coverage",
    "mean_temp",
    "mean_baseline_weight",
]


def load_summary(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    required = ["pen_id", *METRIC_COLS, "n_rows", "n_pigs", "n_barrow", "n_gilt"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"필수 열 누락: {missing}")
    return df.sort_values("pen_id").reset_index(drop=True)


def _save(fig: plt.Figure, outdir: Path, name: str) -> Path:
    path = outdir / name
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"저장: {path}")
    return path


def plot_vitality_bar(df: pd.DataFrame, outdir: Path) -> Path:
    """1) 돈방별 평균 활력도 막대그래프."""
    fig, ax = plt.subplots(figsize=(9, 4.5))
    colors = sns.color_palette("YlGn", n_colors=len(df))
    order = df["mean_vitality"].rank(method="first").astype(int) - 1
    bar_colors = [colors[i] for i in order]
    ax.bar(df["pen_id"], df["mean_vitality"], color=bar_colors, edgecolor="white")
    ax.axhline(df["mean_vitality"].mean(), color="#444444", ls="--", lw=1, label="전체 평균")
    ax.set_title("돈방별 평균 활력도 (mean_vitality)")
    ax.set_xlabel("pen_id")
    ax.set_ylabel("mean_vitality")
    ax.set_ylim(0, max(70, df["mean_vitality"].max() * 1.15))
    ax.legend(frameon=False)
    return _save(fig, outdir, "01_vitality_bar.png")


def plot_grouped_metrics(df: pd.DataFrame, outdir: Path) -> Path:
    """2) 여러 지표를 정규화한 그룹 막대그래프."""
    metrics = ["mean_vitality", "mean_activity", "mean_temp", "mean_baseline_weight"]
    norm = df[metrics].apply(lambda s: (s - s.min()) / (s.max() - s.min() + 1e-9))
    plot_df = norm.assign(pen_id=df["pen_id"]).melt(
        id_vars="pen_id", var_name="metric", value_name="scaled"
    )

    fig, ax = plt.subplots(figsize=(10, 4.8))
    sns.barplot(data=plot_df, x="pen_id", y="scaled", hue="metric", ax=ax, palette="Set2")
    ax.set_title("돈방별 주요 지표 비교 (min-max 정규화 0~1)")
    ax.set_ylabel("scaled value")
    ax.set_xlabel("pen_id")
    ax.legend(title="metric", bbox_to_anchor=(1.02, 1), loc="upper left", frameon=False)
    return _save(fig, outdir, "02_grouped_metrics_bar.png")


def plot_sex_stacked(df: pd.DataFrame, outdir: Path) -> Path:
    """3) 돈방별 성별 구성 누적 막대그래프."""
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.bar(df["pen_id"], df["n_barrow"], label="barrow", color="#4C78A8")
    ax.bar(df["pen_id"], df["n_gilt"], bottom=df["n_barrow"], label="gilt", color="#F58518")
    ax.set_title("돈방별 관찰 행 성별 구성 (n_barrow / n_gilt)")
    ax.set_xlabel("pen_id")
    ax.set_ylabel("n_rows (성별 합)")
    ax.legend(frameon=False)
    return _save(fig, outdir, "03_sex_stacked_bar.png")


def plot_scatter_temp_vitality(df: pd.DataFrame, outdir: Path) -> Path:
    """4) 온도 vs 활력도 산점도 (점 크기=활동량)."""
    fig, ax = plt.subplots(figsize=(7.5, 5.5))
    sizes = 80 + 4 * (df["mean_activity"] - df["mean_activity"].min())
    sc = ax.scatter(
        df["mean_temp"],
        df["mean_vitality"],
        s=sizes,
        c=df["mean_cough"],
        cmap="YlOrRd",
        edgecolors="#333333",
        alpha=0.9,
    )
    for _, row in df.iterrows():
        ax.annotate(row["pen_id"], (row["mean_temp"], row["mean_vitality"]),
                    textcoords="offset points", xytext=(6, 4), fontsize=9)
    cbar = fig.colorbar(sc, ax=ax)
    cbar.set_label("mean_cough")
    ax.set_title("온도 vs 활력도 (크기=활동량, 색=기침)")
    ax.set_xlabel("mean_temp (°C)")
    ax.set_ylabel("mean_vitality")
    return _save(fig, outdir, "04_scatter_temp_vitality.png")


def plot_heatmap(df: pd.DataFrame, outdir: Path) -> Path:
    """5) 돈방 × 지표 히트맵 (열별 z-score)."""
    mat = df.set_index("pen_id")[METRIC_COLS]
    z = (mat - mat.mean()) / mat.std(ddof=0)

    fig, ax = plt.subplots(figsize=(9, 4.8))
    sns.heatmap(
        z,
        annot=mat.round(2),
        fmt="",
        cmap="RdYlGn",
        center=0,
        linewidths=0.5,
        ax=ax,
        cbar_kws={"label": "z-score"},
    )
    ax.set_title("돈방별 지표 히트맵 (색=z-score, 숫자=원값)")
    ax.set_xlabel("")
    ax.set_ylabel("pen_id")
    return _save(fig, outdir, "05_metrics_heatmap.png")


def plot_radar(df: pd.DataFrame, outdir: Path) -> Path:
    """6) 레이더 차트 — 돈방별 다지표 프로파일."""
    metrics = ["mean_vitality", "mean_activity", "mean_coverage", "mean_temp", "mean_baseline_weight"]
    # cough는 낮을수록 좋게 보이도록 반전해 스케일
    raw = df[metrics].copy()
    raw["low_cough"] = -df["mean_cough"]
    labels = metrics + ["low_cough"]
    scaled = raw.apply(lambda s: (s - s.min()) / (s.max() - s.min() + 1e-9))

    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False)
    angles = np.concatenate([angles, angles[:1]])

    n = len(df)
    ncols = 4
    nrows = int(np.ceil(n / ncols))
    fig, axes = plt.subplots(
        nrows, ncols, figsize=(12, 2.8 * nrows), subplot_kw={"polar": True}
    )
    axes = np.atleast_1d(axes).ravel()

    for i, row in df.iterrows():
        ax = axes[i]
        values = scaled.loc[i, labels].to_numpy()
        values = np.concatenate([values, values[:1]])
        ax.plot(angles, values, color="#2A9D8F", lw=1.8)
        ax.fill(angles, values, color="#2A9D8F", alpha=0.25)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels([l.replace("mean_", "") for l in labels], fontsize=7)
        ax.set_yticklabels([])
        ax.set_ylim(0, 1)
        ax.set_title(row["pen_id"], fontsize=11, pad=10)

    for j in range(n, len(axes)):
        axes[j].set_visible(False)

    fig.suptitle("돈방별 지표 레이더 (정규화 0~1, low_cough=기침 낮을수록 높음)", y=1.02)
    return _save(fig, outdir, "06_radar_by_pen.png")


def plot_lollipop_activity(df: pd.DataFrame, outdir: Path) -> Path:
    """7) 활동량 롤리팝(수평) 차트."""
    ordered = df.sort_values("mean_activity")
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.hlines(ordered["pen_id"], 0, ordered["mean_activity"], color="#94A3B8", lw=2)
    ax.plot(ordered["mean_activity"], ordered["pen_id"], "o", color="#0F766E", markersize=9)
    ax.set_title("돈방별 평균 활동시간 (mean_activity)")
    ax.set_xlabel("mean_activity (분/일)")
    ax.set_ylabel("pen_id")
    ax.set_xlim(0, ordered["mean_activity"].max() * 1.1)
    return _save(fig, outdir, "07_activity_lollipop.png")


def plot_pair_relations(df: pd.DataFrame, outdir: Path) -> Path:
    """8) 주요 수치열 pairwise 산점도 행렬."""
    cols = ["mean_vitality", "mean_activity", "mean_temp", "mean_cough", "mean_baseline_weight"]
    g = sns.pairplot(
        df[cols],
        corner=True,
        diag_kind="hist",
        plot_kws={"s": 70, "color": "#3B82F6", "edgecolor": "white"},
        diag_kws={"color": "#93C5FD", "edgecolor": "white"},
    )
    g.fig.suptitle("주요 지표 pairwise 관계", y=1.02)
    path = outdir / "08_pairplot.png"
    g.fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(g.fig)
    print(f"저장: {path}")
    return path


def plot_coverage_vs_rows(df: pd.DataFrame, outdir: Path) -> Path:
    """9) 관측 수 vs 카메라 커버리지 버블 차트."""
    fig, ax = plt.subplots(figsize=(7.5, 5))
    sizes = 300 * (df["n_pigs"] / df["n_pigs"].max())
    ax.scatter(
        df["n_rows"],
        df["mean_coverage"],
        s=sizes,
        c=df["mean_vitality"],
        cmap="viridis",
        edgecolors="#222222",
        alpha=0.85,
    )
    for _, row in df.iterrows():
        ax.annotate(row["pen_id"], (row["n_rows"], row["mean_coverage"]),
                    textcoords="offset points", xytext=(5, 4), fontsize=9)
    cbar = fig.colorbar(ax.collections[0], ax=ax)
    cbar.set_label("mean_vitality")
    ax.set_title("관측 행 수 vs 카메라 커버리지 (크기=n_pigs)")
    ax.set_xlabel("n_rows")
    ax.set_ylabel("mean_coverage (%)")
    return _save(fig, outdir, "09_bubble_rows_coverage.png")


def plot_dashboard(df: pd.DataFrame, outdir: Path) -> Path:
    """10) 한 장 요약 대시보드."""
    fig = plt.figure(figsize=(12, 8))
    gs = fig.add_gridspec(2, 2, hspace=0.35, wspace=0.28)

    ax1 = fig.add_subplot(gs[0, 0])
    ax1.bar(df["pen_id"], df["mean_vitality"], color="#2A9D8F")
    ax1.set_title("평균 활력도")
    ax1.tick_params(axis="x", rotation=45)

    ax2 = fig.add_subplot(gs[0, 1])
    ax2.bar(df["pen_id"], df["mean_activity"], color="#E9C46A")
    ax2.set_title("평균 활동시간")
    ax2.tick_params(axis="x", rotation=45)

    ax3 = fig.add_subplot(gs[1, 0])
    ax3.plot(df["pen_id"], df["mean_temp"], "o-", color="#E76F51", label="temp")
    ax3.set_ylabel("mean_temp")
    ax3b = ax3.twinx()
    ax3b.plot(df["pen_id"], df["mean_cough"], "s--", color="#264653", label="cough")
    ax3b.set_ylabel("mean_cough")
    ax3.set_title("온도 · 기침")
    ax3.tick_params(axis="x", rotation=45)
    lines1, labels1 = ax3.get_legend_handles_labels()
    lines2, labels2 = ax3b.get_legend_handles_labels()
    ax3.legend(lines1 + lines2, labels1 + labels2, frameon=False, fontsize=8)

    ax4 = fig.add_subplot(gs[1, 1])
    width = 0.4
    x = np.arange(len(df))
    ax4.bar(x - width / 2, df["n_barrow"], width, label="barrow", color="#4C78A8")
    ax4.bar(x + width / 2, df["n_gilt"], width, label="gilt", color="#F58518")
    ax4.set_xticks(x)
    ax4.set_xticklabels(df["pen_id"], rotation=45)
    ax4.set_title("성별 구성")
    ax4.legend(frameon=False, fontsize=8)

    fig.suptitle("돈방 요약 대시보드 (pipeline_summary_by_pen)", fontsize=13, y=0.98)
    path = outdir / "10_dashboard.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"저장: {path}")
    return path


def run_all(csv_path: Path, outdir: Path) -> list[Path]:
    outdir.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", context="notebook")
    font_name = _configure_korean_font()
    print(f"한글 폰트: {font_name or '(미설정 — 제목이 깨질 수 있음)'}")

    df = load_summary(csv_path)
    print(f"입력: {csv_path}  shape={df.shape}")
    print(df.to_string(index=False))

    paths = [
        plot_vitality_bar(df, outdir),
        plot_grouped_metrics(df, outdir),
        plot_sex_stacked(df, outdir),
        plot_scatter_temp_vitality(df, outdir),
        plot_heatmap(df, outdir),
        plot_radar(df, outdir),
        plot_lollipop_activity(df, outdir),
        plot_pair_relations(df, outdir),
        plot_coverage_vs_rows(df, outdir),
        plot_dashboard(df, outdir),
    ]
    print(f"\n총 {len(paths)}개 figure 저장 → {outdir}")
    return paths


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="돈방 요약 CSV를 다양한 plot으로 시각화")
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--outdir", type=Path, default=DEFAULT_OUTDIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_all(args.csv.resolve(), args.outdir.resolve())


if __name__ == "__main__":
    main()
