"""
집단별 response 요약통계 (n, mean, sd)

CSV 열: sample_id, group, batch, time_min, response, valid
규칙:
  - valid=True 인 행만 분석에 사용
  - 원본 CSV는 읽기만 하고 수정하지 않음
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

REQUIRED_COLS = ["sample_id", "group", "batch", "time_min", "response", "valid"]
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CSV = ROOT / "data" / "examples" / "group_response_demo.csv"


def step1_load(csv_path: Path) -> pd.DataFrame:
    """
    1단계: CSV 읽기 (원본 파일은 변경하지 않음)

    입력: csv_path (파일 경로)
    출력: DataFrame df_raw — 원본과 동일한 내용의 메모리 복사본
    """
    print("=" * 60)
    print("[1] CSV 읽기")
    print("=" * 60)
    print(f"입력: {csv_path}")

    if not csv_path.exists():
        raise FileNotFoundError(f"CSV 파일이 없습니다: {csv_path}")

    df_raw = pd.read_csv(csv_path)
    print(f"출력: shape={df_raw.shape} (행={df_raw.shape[0]}, 열={df_raw.shape[1]})")
    print(f"열 이름: {list(df_raw.columns)}")
    print(f"앞 5행:\n{df_raw.head()}")
    return df_raw


def step2_check_schema(df_raw: pd.DataFrame) -> None:
    """
    2단계: 필수 열 존재 여부 확인

    입력: df_raw
    출력: 없음 (실패 시 ValueError)
    """
    print("\n" + "=" * 60)
    print("[2] 스키마(필수 열) 검사")
    print("=" * 60)
    print(f"입력: 열={list(df_raw.columns)}")

    missing = [c for c in REQUIRED_COLS if c not in df_raw.columns]
    if missing:
        raise ValueError(f"필수 열 누락: {missing}")

    print(f"출력: 필수 열 모두 존재 {REQUIRED_COLS}")


def step3_check_missing(df_raw: pd.DataFrame) -> pd.Series:
    """
    3단계: 결측 검사

    입력: df_raw
    출력: missing_counts — 열별 결측 개수 (Series)
    """
    print("\n" + "=" * 60)
    print("[3] 결측 검사")
    print("=" * 60)
    print(f"입력: shape={df_raw.shape}")

    missing_counts = df_raw[REQUIRED_COLS].isna().sum()
    print("출력: 열별 결측 수")
    print(missing_counts.to_string())
    print(f"\n결측이 있는 행 수(어느 열이든): {df_raw[REQUIRED_COLS].isna().any(axis=1).sum()}")
    return missing_counts


def step4_check_duplicates(df_raw: pd.DataFrame) -> dict[str, int]:
    """
    4단계: 중복 검사

    입력: df_raw
    출력: dup_report — 전체행 중복 / sample_id 중복 건수
    """
    print("\n" + "=" * 60)
    print("[4] 중복 검사")
    print("=" * 60)
    print(f"입력: shape={df_raw.shape}")

    n_full_dup = int(df_raw.duplicated(keep=False).sum())
    n_id_dup = int(df_raw.duplicated(subset=["sample_id"], keep=False).sum())

    dup_report = {
        "n_rows_in_full_duplicate_groups": n_full_dup,
        "n_rows_in_sample_id_duplicate_groups": n_id_dup,
        "n_full_duplicate_pairs_extra": int(df_raw.duplicated().sum()),
        "n_sample_id_duplicate_extras": int(df_raw.duplicated(subset=["sample_id"]).sum()),
    }

    print("출력:")
    for k, v in dup_report.items():
        print(f"  {k}: {v}")

    if n_full_dup > 0:
        print("\n전체 행 중복 예시:")
        print(df_raw[df_raw.duplicated(keep=False)].head(10))
    if n_id_dup > 0:
        print("\nsample_id 중복 예시:")
        print(df_raw[df_raw.duplicated(subset=["sample_id"], keep=False)].head(10))

    return dup_report


def step5_filter_valid(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    5단계: valid=True 행만 선택 (원본 df_raw는 변경하지 않음)

    입력: df_raw
    출력: df_valid — valid=True 인 행의 복사본
    """
    print("\n" + "=" * 60)
    print("[5] valid=True 필터")
    print("=" * 60)
    print(f"입력: shape={df_raw.shape}")
    print(f"valid 값 분포:\n{df_raw['valid'].value_counts(dropna=False)}")

    # 문자열 'True'/'False'로 읽힌 경우도 허용
    valid_mask = df_raw["valid"].astype(str).str.strip().str.lower().isin(["true", "1"])
    df_valid = df_raw.loc[valid_mask].copy()

    print(f"출력: shape={df_valid.shape} (제외 {df_raw.shape[0] - df_valid.shape[0]}행)")
    print("원본 df_raw는 수정되지 않음 (copy 사용).")
    return df_valid


def step6_group_summary(df_valid: pd.DataFrame) -> pd.DataFrame:
    """
    6단계: 집단(group)별 n, mean, sd 계산

    입력: df_valid (valid=True 행)
    출력: summary — group, n, mean, sd
      - n: response가 비결측인 관측 수
      - mean / sd: response의 표본 평균 / 표본 표준편차 (ddof=1)
    """
    print("\n" + "=" * 60)
    print("[6] 집단별 n · mean · sd")
    print("=" * 60)
    print(f"입력: shape={df_valid.shape}, 분석열=response, 집단열=group")

    # response 결측은 집계에서 자동 제외되지만, n을 명시적으로 비결측 기준으로 맞춤
    summary = (
        df_valid.groupby("group", as_index=False)["response"]
        .agg(n="count", mean="mean", sd=lambda s: s.std(ddof=1))
        .round({"mean": 4, "sd": 4})
    )

    print("출력: 집단별 요약표")
    print(summary.to_string(index=False))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="valid=True 행만 사용해 집단별 response n/mean/sd를 계산합니다."
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=DEFAULT_CSV,
        help=f"입력 CSV 경로 (기본: {DEFAULT_CSV})",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="요약표 저장 경로 (지정 시에만 저장; 원본 CSV는 절대 덮어쓰지 않음)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    csv_path = args.csv.resolve()

    # --- 단계별 파이프라인 (원본 파일은 읽기만 함) ---
    df_raw = step1_load(csv_path)
    step2_check_schema(df_raw)
    step3_check_missing(df_raw)
    step4_check_duplicates(df_raw)
    df_valid = step5_filter_valid(df_raw)
    summary = step6_group_summary(df_valid)

    print("\n" + "=" * 60)
    print("[완료] 원본 파일 미수정 확인")
    print("=" * 60)
    print(f"읽은 파일: {csv_path}")
    print("이 스크립트는 원본 CSV에 to_csv/쓰기 작업을 하지 않습니다.")

    if args.out is not None:
        out_path = args.out.resolve()
        if out_path == csv_path:
            raise ValueError("요약 결과를 원본 CSV 경로에 저장할 수 없습니다.")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        summary.to_csv(out_path, index=False)
        print(f"요약표 저장: {out_path}")


if __name__ == "__main__":
    main()
