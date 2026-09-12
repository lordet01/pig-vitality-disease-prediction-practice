"""
Load → Inspect → filter → merge → groupby → export

두 원자료 CSV를 읽어 품질 필터 후 병합·집계하고, 결과 CSV 1개를 저장한다.
원본 CSV는 읽기만 하며 수정하지 않는다.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OBS = ROOT / "data" / "raw" / "pig_daily_observations.csv"
DEFAULT_META = ROOT / "data" / "raw" / "pig_metadata.csv"
DEFAULT_OUT = ROOT / "results" / "pipeline_summary_by_pen.csv"

OBS_KEY_COLS = ["pig_id", "observation_date"]
META_KEY_COLS = ["pig_id"]
KEY_VIDEO_COLS = ["activity_minutes", "distance_m", "lying_ratio", "feeding_minutes"]


def step1_load(obs_path: Path, meta_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """1. Load — 두 CSV 로드 (utf-8-sig로 BOM 대응)."""
    print("=" * 60)
    print("[1] Load")
    print("=" * 60)

    for path in (obs_path, meta_path):
        if not path.exists():
            raise FileNotFoundError(f"CSV 파일이 없습니다: {path}")

    df_obs = pd.read_csv(obs_path, encoding="utf-8-sig", parse_dates=["observation_date"])
    df_meta = pd.read_csv(meta_path, encoding="utf-8-sig", parse_dates=["birth_date", "arrival_date"])

    print(f"observations: {obs_path}")
    print(f"  shape={df_obs.shape}, columns={list(df_obs.columns)}")
    print(f"metadata: {meta_path}")
    print(f"  shape={df_meta.shape}, columns={list(df_meta.columns)}")
    return df_obs, df_meta


def step2_inspect(df_obs: pd.DataFrame, df_meta: pd.DataFrame) -> None:
    """2. Inspect — 구조·중복·결측·QC 점검 (변환 없음)."""
    print("\n" + "=" * 60)
    print("[2] Inspect")
    print("=" * 60)

    print("\n--- observations ---")
    print(f"shape: {df_obs.shape}")
    print(f"pig_id 수: {df_obs['pig_id'].nunique()}")
    print(f"pen_id 수: {df_obs['pen_id'].nunique()}")
    print(
        f"날짜 범위: {df_obs['observation_date'].min().date()} "
        f"~ {df_obs['observation_date'].max().date()}"
    )
    n_dup = int(df_obs.duplicated(OBS_KEY_COLS).sum())
    print(f"(pig_id, observation_date) 중복 행: {n_dup}")

    missing = df_obs.isna().sum()
    miss = missing[missing > 0].sort_values(ascending=False)
    print("결측 열:")
    print(miss.to_string() if len(miss) else "  (없음)")
    print("valid:\n", df_obs["valid"].value_counts(dropna=False).to_string())
    print("qc_note:\n", df_obs["qc_note"].fillna("no_note").value_counts().to_string())

    print("\n--- metadata ---")
    print(f"shape: {df_meta.shape}")
    print(f"pig_id 수: {df_meta['pig_id'].nunique()}")
    print(f"pig_id 중복: {int(df_meta.duplicated(META_KEY_COLS).sum())}")

    obs_ids = set(df_obs["pig_id"])
    meta_ids = set(df_meta["pig_id"])
    print(f"obs에만 있는 pig_id: {len(obs_ids - meta_ids)}")
    print(f"meta에만 있는 pig_id: {len(meta_ids - obs_ids)}")


def step3_filter(df_obs: pd.DataFrame) -> pd.DataFrame:
    """3. filter — 실험계획서 제외 기준으로 관찰자료 정제."""
    print("\n" + "=" * 60)
    print("[3] filter")
    print("=" * 60)

    df = df_obs.copy()
    n0 = len(df)
    print(f"시작 행 수: {n0}")

    before = len(df)
    df = df.drop_duplicates(OBS_KEY_COLS, keep="first")
    print(f"[1] 중복 제거: {before - len(df)}행 제외 → {len(df)}")

    # 문자열 'True'/'False'로 읽힌 경우도 허용
    valid_mask = df["valid"].astype(str).str.strip().str.lower().isin(["true", "1"])
    before = len(df)
    df = df.loc[valid_mask].copy()
    print(f"[2] valid=False 제외: {before - len(df)}행 제외 → {len(df)}")

    before = len(df)
    df = df.loc[df["camera_coverage_pct"] >= 70]
    print(f"[3] camera_coverage_pct < 70 제외: {before - len(df)}행 제외 → {len(df)}")

    before = len(df)
    range_ok = (
        (df["distance_m"].isna() | (df["distance_m"] >= 0))
        & (df["lying_ratio"].isna() | df["lying_ratio"].between(0, 1))
        & df["camera_coverage_pct"].between(0, 100)
    )
    df = df.loc[range_ok]
    print(f"[4] 범위 오류 제외: {before - len(df)}행 제외 → {len(df)}")

    before = len(df)
    df = df.dropna(subset=KEY_VIDEO_COLS)
    print(f"[5] 핵심 영상변수 결측 제외: {before - len(df)}행 제외 → {len(df)}")

    df = df.reset_index(drop=True)
    print(f"최종 filter: {n0} → {len(df)} (제외 {n0 - len(df)}행)")
    return df


def step4_merge(df_obs_clean: pd.DataFrame, df_meta: pd.DataFrame) -> pd.DataFrame:
    """4. merge — pig_id 기준 many_to_one 병합."""
    print("\n" + "=" * 60)
    print("[4] merge")
    print("=" * 60)

    if df_meta.duplicated("pig_id").any():
        raise ValueError("metadata의 pig_id가 고유하지 않아 many_to_one 병합이 불가합니다.")

    # observations의 pen_id와 충돌을 피하기 위해 metadata의만 남김
    meta_cols = [c for c in df_meta.columns if c != "pen_id"]
    df_merged = df_obs_clean.merge(
        df_meta[meta_cols],
        on="pig_id",
        how="inner",
        validate="many_to_one",
    )

    n_before = len(df_obs_clean)
    n_after = len(df_merged)
    print(f"조인 키: pig_id (validate=many_to_one)")
    print(f"filter 후 행: {n_before} → merge 후 행: {n_after}")
    print(f"메타 미매칭으로 제외: {n_before - n_after}")
    print(f"병합 열: {list(df_merged.columns)}")
    print(f"앞 3행:\n{df_merged.head(3)}")
    return df_merged


def step5_groupby(df_merged: pd.DataFrame) -> pd.DataFrame:
    """5. groupby — 돈방별 요약 집계."""
    print("\n" + "=" * 60)
    print("[5] groupby")
    print("=" * 60)
    print(f"입력 shape: {df_merged.shape}")

    summary = (
        df_merged.groupby("pen_id", as_index=False)
        .agg(
            n_rows=("pig_id", "size"),
            n_pigs=("pig_id", "nunique"),
            mean_vitality=("vitality_score", "mean"),
            mean_activity=("activity_minutes", "mean"),
            mean_cough=("cough_events", "mean"),
            mean_coverage=("camera_coverage_pct", "mean"),
            mean_temp=("ambient_temp_c", "mean"),
            mean_baseline_weight=("baseline_weight_kg", "mean"),
            n_barrow=("sex", lambda s: (s == "barrow").sum()),
            n_gilt=("sex", lambda s: (s == "gilt").sum()),
        )
        .round(2)
        .sort_values("pen_id")
        .reset_index(drop=True)
    )

    print("돈방별 요약:")
    print(summary.to_string(index=False))
    return summary


def step6_export(summary: pd.DataFrame, out_path: Path) -> Path:
    """6. export — 집계 결과 CSV 1개 저장."""
    print("\n" + "=" * 60)
    print("[6] export")
    print("=" * 60)

    out_path = out_path.resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(out_path, index=False)

    print(f"저장: {out_path}")
    print(f"shape={summary.shape}, columns={list(summary.columns)}")
    return out_path


def run_pipeline(
    obs_path: Path,
    meta_path: Path,
    out_path: Path,
) -> Path:
    """Load → Inspect → filter → merge → groupby → export 전체 실행."""
    df_obs, df_meta = step1_load(obs_path, meta_path)
    step2_inspect(df_obs, df_meta)
    df_clean = step3_filter(df_obs)
    df_merged = step4_merge(df_clean, df_meta)
    summary = step5_groupby(df_merged)
    return step6_export(summary, out_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="두 CSV를 Load→Inspect→filter→merge→groupby→export 합니다."
    )
    parser.add_argument("--obs", type=Path, default=DEFAULT_OBS, help="일별 관찰 CSV")
    parser.add_argument("--meta", type=Path, default=DEFAULT_META, help="개체 메타데이터 CSV")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="출력 CSV 경로")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    out = run_pipeline(args.obs.resolve(), args.meta.resolve(), args.out)
    print("\n" + "=" * 60)
    print("[완료]")
    print("=" * 60)
    print(f"출력 CSV: {out}")
    print("원본 CSV는 수정되지 않았습니다.")


if __name__ == "__main__":
    main()
