from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
CLEAN = ROOT / "data" / "clean"

observations = pd.read_csv(RAW / "pig_daily_observations.csv")
metadata = pd.read_csv(RAW / "pig_metadata.csv")
events = pd.read_csv(RAW / "disease_events.csv")
practice = pd.read_csv(CLEAN / "practice_dataset.csv")

print("observations:", observations.shape)
print("metadata:", metadata.shape)
print("events:", events.shape)
print("practice:", practice.shape)

print("\nDuplicate pig-days:")
print(observations.duplicated(["pig_id", "observation_date"]).sum())

print("\nMissing values in raw observations:")
print(observations.isna().sum().sort_values(ascending=False).head(10))

print("\nQC notes:")
print(observations["qc_note"].fillna("no_note").value_counts())

print("\nTarget by split:")
print(practice.groupby("split")["disease_next_3d"].agg(["size", "sum", "mean"]))

# TODO 1: 데이터 품질 보고 4문장을 작성하세요.
# TODO 2: M0, M1, M2의 feature 목록을 정의하세요.
# TODO 3: validation에서 임계값을 결정하세요.
# TODO 4: test 결과와 현장 경보량을 보고하세요.

