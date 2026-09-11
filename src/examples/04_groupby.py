"""4단계: groupby — 돈방·날짜·개체 단위 집계"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "examples"

df = pd.read_pickle(OUT / "03_clean.pkl")

print("=" * 60)
print("[04] groupby")
print("=" * 60)
print(f"입력 shape: {df.shape}")

# A) 돈방별 요약
by_pen = (
    df.groupby("pen_id", as_index=False)
    .agg(
        n_rows=("pig_id", "size"),
        n_pigs=("pig_id", "nunique"),
        mean_vitality=("vitality_score", "mean"),
        mean_activity=("activity_minutes", "mean"),
        mean_cough=("cough_events", "mean"),
        mean_coverage=("camera_coverage_pct", "mean"),
        mean_temp=("ambient_temp_c", "mean"),
    )
    .round(2)
)
print("\n--- A) 돈방별 요약 ---\n", by_pen)

# B) 날짜별 전체 평균 활력도
by_date = (
    df.groupby("observation_date", as_index=False)
    .agg(
        n_pigs=("pig_id", "nunique"),
        mean_vitality=("vitality_score", "mean"),
        mean_temp=("ambient_temp_c", "mean"),
        mean_humidity=("humidity_pct", "mean"),
    )
)
by_date[["mean_vitality", "mean_temp", "mean_humidity"]] = (
    by_date[["mean_vitality", "mean_temp", "mean_humidity"]].round(2)
)
print("\n--- B) 날짜별 요약 (앞 7일) ---\n", by_date.head(7))
print("\n--- B) 날짜별 요약 (뒤 3일) ---\n", by_date.tail(3))

# C) 돈방 × 날짜 관측 수 (결측·제외 후 밀도 확인)
pen_date = (
    df.groupby(["pen_id", "observation_date"], as_index=False)
    .size()
    .rename(columns={"size": "n_obs"})
)
print("\n--- C) 돈방×날짜 관측 수 분포 ---")
print(pen_date["n_obs"].describe().round(2))
print(pen_date.head(8))

# D) 개체별 활력도 요약 (후속 분석용)
by_pig = (
    df.groupby("pig_id", as_index=False)
    .agg(
        pen_id=("pen_id", "first"),
        n_days=("observation_date", "nunique"),
        mean_vitality=("vitality_score", "mean"),
        min_vitality=("vitality_score", "min"),
        max_vitality=("vitality_score", "max"),
        total_cough=("cough_events", "sum"),
    )
    .round(2)
)
print("\n--- D) 개체별 요약 (앞 5두) ---\n", by_pig.head())

by_pen.to_pickle(OUT / "04_by_pen.pkl")
by_date.to_pickle(OUT / "04_by_date.pkl")
by_pig.to_pickle(OUT / "04_by_pig.pkl")
print(f"\n중간결과 저장: 04_by_pen.pkl, 04_by_date.pkl, 04_by_pig.pkl")
