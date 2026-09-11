"""2단계: inspect — 구조·중복·결측·QC 점검"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "examples"

df = pd.read_pickle(OUT / "01_raw.pkl")

print("=" * 60)
print("[02] inspect")
print("=" * 60)

print("\n--- 기본 정보 ---")
print(f"shape: {df.shape}")
print(f"pig_id 수: {df['pig_id'].nunique()}")
print(f"pen_id 수: {df['pen_id'].nunique()}")
print(f"날짜 범위: {df['observation_date'].min().date()} ~ {df['observation_date'].max().date()}")
print(f"관찰일 수: {df['observation_date'].nunique()}")

print("\n--- (pig_id, observation_date) 중복 ---")
n_dup = df.duplicated(["pig_id", "observation_date"]).sum()
print(f"중복 행 수: {n_dup}")
if n_dup:
    print(df.loc[df.duplicated(["pig_id", "observation_date"], keep=False)]
            .sort_values(["pig_id", "observation_date"])
            .head(10))

print("\n--- 열별 결측 ---")
missing = df.isna().sum().sort_values(ascending=False)
missing_pct = (df.isna().mean() * 100).round(2)
miss_table = pd.DataFrame({"n_missing": missing, "pct": missing_pct})
print(miss_table.loc[miss_table["n_missing"] > 0])

print("\n--- valid / qc_note ---")
print("valid:\n", df["valid"].value_counts(dropna=False))
print("\nqc_note:\n", df["qc_note"].fillna("no_note").value_counts())

print("\n--- 범위 이상치 (실험계획서 기준) ---")
print(f"distance_m < 0: {(df['distance_m'] < 0).sum()}")
print(f"lying_ratio 범위 밖: {((df['lying_ratio'] < 0) | (df['lying_ratio'] > 1)).sum()}")
print(f"camera_coverage_pct 범위 밖: {((df['camera_coverage_pct'] < 0) | (df['camera_coverage_pct'] > 100)).sum()}")
print(f"camera_coverage_pct < 70: {(df['camera_coverage_pct'] < 70).sum()}")

print("\n--- 수치형 describe (일부) ---")
print(df[["weight_kg", "activity_minutes", "distance_m", "lying_ratio",
          "vitality_score", "camera_coverage_pct"]].describe().round(2))

# inspect는 변환 없이 다음 단계가 raw를 그대로 쓰도록 표시만
print(f"\n입력 유지: {OUT / '01_raw.pkl'} (inspect는 변환 없음)")
