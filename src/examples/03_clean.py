"""3단계: clean — 실험계획서 제외 기준으로 정제"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "examples"

df = pd.read_pickle(OUT / "01_raw.pkl")
n0 = len(df)

print("=" * 60)
print("[03] clean")
print("=" * 60)
print(f"시작 행 수: {n0}")

# 1) (pig_id, observation_date) 완전 중복 제거
before = len(df)
df = df.drop_duplicates(["pig_id", "observation_date"], keep="first")
print(f"\n[1] 중복 제거: {before - len(df)}행 제외 → {len(df)}")

# 2) valid=False 제외
before = len(df)
invalid = df.loc[~df["valid"], ["pig_id", "observation_date", "qc_note"]]
print(f"\n[2] valid=False 사유:\n{invalid.to_string(index=False)}")
df = df.loc[df["valid"]].copy()
print(f"제외 {before - len(df)}행 → {len(df)}")

# 3) 카메라 커버리지 70% 미만 제외
before = len(df)
low_cov = (df["camera_coverage_pct"] < 70).sum()
df = df.loc[df["camera_coverage_pct"] >= 70]
print(f"\n[3] camera_coverage_pct < 70: {low_cov}행 제외 → {len(df)}")

# 4) 범위 오류 제외
before = len(df)
range_ok = (
    (df["distance_m"].isna() | (df["distance_m"] >= 0))
    & (df["lying_ratio"].isna() | ((df["lying_ratio"] >= 0) & (df["lying_ratio"] <= 1)))
    & (df["camera_coverage_pct"].between(0, 100))
)
df = df.loc[range_ok]
print(f"\n[4] 범위 오류: {before - len(df)}행 제외 → {len(df)}")

# 5) 핵심 영상변수 결측 행 제외
key_cols = ["activity_minutes", "distance_m", "lying_ratio", "feeding_minutes"]
before = len(df)
n_key_na = df[key_cols].isna().any(axis=1).sum()
df = df.dropna(subset=key_cols)
print(f"\n[5] 핵심 영상변수 결측({key_cols}): {n_key_na}행 제외 → {len(df)}")

# 정리: 사용하지 않는 QC 열은 남겨두되 인덱스 재설정
df = df.reset_index(drop=True)

print(f"\n최종 정제 결과: {n0} → {len(df)} (제외 {n0 - len(df)}행, {100 * (n0 - len(df)) / n0:.2f}%)")
print(f"\n정제 후 앞 5행:\n{df.head()}")
print(f"\n정제 후 결측 남은 열:\n{df.isna().sum().loc[lambda s: s > 0]}")

df.to_pickle(OUT / "03_clean.pkl")
df.to_csv(OUT / "03_clean.csv", index=False)
print(f"\n중간결과 저장: {OUT / '03_clean.pkl'}, {OUT / '03_clean.csv'}")
