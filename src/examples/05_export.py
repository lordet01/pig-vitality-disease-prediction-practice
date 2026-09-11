"""5단계: export — 정제·집계 결과 CSV로 내보내기"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "examples"
OUT.mkdir(parents=True, exist_ok=True)

clean = pd.read_pickle(OUT / "03_clean.pkl")
by_pen = pd.read_pickle(OUT / "04_by_pen.pkl")
by_date = pd.read_pickle(OUT / "04_by_date.pkl")
by_pig = pd.read_pickle(OUT / "04_by_pig.pkl")

print("=" * 60)
print("[05] export")
print("=" * 60)

paths = {
    "clean_observations.csv": clean,
    "summary_by_pen.csv": by_pen,
    "summary_by_date.csv": by_date,
    "summary_by_pig.csv": by_pig,
}

for name, frame in paths.items():
    path = OUT / name
    frame.to_csv(path, index=False)
    print(f"저장: {path}")
    print(f"  shape={frame.shape}, columns={list(frame.columns)[:6]}...")
    print(f"  미리보기:\n{frame.head(3)}\n")

# 파이프라인 요약
raw_n = 5045  # 01_read_csv 기준 (실행 시 실제 값으로 대체 가능)
print("--- 파이프라인 요약 ---")
print(f"clean 행 수: {len(clean)}")
print(f"돈방 집계 행 수: {len(by_pen)}")
print(f"날짜 집계 행 수: {len(by_date)}")
print(f"개체 집계 행 수: {len(by_pig)}")
print(f"\n모든 export 파일 위치: {OUT}")
