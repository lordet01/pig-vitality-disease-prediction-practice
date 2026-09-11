"""1단계: read_csv — 원자료 CSV 읽기"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "pig_daily_observations.csv"
OUT = ROOT / "data" / "examples"
OUT.mkdir(parents=True, exist_ok=True)

# 날짜 열은 parse_dates로 datetime으로 읽기
df = pd.read_csv(RAW, parse_dates=["observation_date"])

print("=" * 60)
print("[01] read_csv")
print("=" * 60)
print(f"파일: {RAW}")
print(f"shape: {df.shape}  (행={df.shape[0]}, 열={df.shape[1]})")
print(f"\n열 이름:\n{list(df.columns)}")
print(f"\ndtypes:\n{df.dtypes}")
print(f"\n앞 5행:\n{df.head()}")
print(f"\n뒤 3행:\n{df.tail(3)}")

# 다음 단계용 중간 저장
df.to_pickle(OUT / "01_raw.pkl")
print(f"\n중간결과 저장: {OUT / '01_raw.pkl'}")
