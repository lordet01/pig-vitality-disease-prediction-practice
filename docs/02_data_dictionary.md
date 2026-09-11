# 데이터 사전

## 파일 관계

- `pig_metadata.csv`: 개체당 1행
- `pig_daily_observations.csv`: 개체-일당 1행을 의도한 원자료. 중복·결측·오류가 일부 포함됨
- `disease_events.csv`: 수의사 확인 질병 이벤트당 1행
- `practice_dataset.csv`: 정제·라벨 결합·과거 변화량 계산이 끝난 입문용 자료

조인 키는 `pig_id`, 반복측정 키는 `(pig_id, observation_date)`다.

## pig_metadata.csv

| 열 | 의미 | 단위·범주 |
|---|---|---|
| pig_id | 합성 개체 ID | P001~P120 |
| pen_id | 돈방 ID | PEN01~PEN08 |
| sex | 성별 | barrow, gilt |
| breed | 합성 품종 구분 | LYD, YLD |
| birth_date | 출생일 | YYYY-MM-DD |
| arrival_date | 연구시설 입식일 | YYYY-MM-DD |
| baseline_weight_kg | 관찰 전 기준체중 | kg |

## pig_daily_observations.csv

| 열 | 의미 | 단위·범주 | 품질 기준 |
|---|---|---|---|
| observation_date | 관찰일 | 날짜 | 연구기간 내 |
| pig_id | 개체 ID | 문자열 | metadata와 일치 |
| pen_id | 돈방 ID | 문자열 | metadata와 일치 |
| age_days | 일령 | 일 | 양수 |
| weight_kg | 추정 체중 | kg | 20~120 예상 |
| activity_minutes | 하루 활동시간 | 분/일 | 0 이상 |
| distance_m | 하루 이동거리 | m/일 | 0 이상 |
| mean_speed_m_s | 활동 중 평균속도 | m/s | 0 이상 |
| lying_ratio | 누워 있는 시간 비율 | 0~1 | 범위 확인 |
| feeding_visits | 급이기 방문 횟수 | 회/일 | 0 이상 정수 |
| feeding_minutes | 급이 행동시간 | 분/일 | 0 이상 |
| drinking_visits | 음수기 방문 횟수 | 회/일 | 0 이상 정수 |
| social_contacts | 근접·접촉 이벤트 | 회/일 | 0 이상 정수 |
| posture_changes | 기립·눕기 변화 | 회/일 | 0 이상 정수 |
| cough_events | 기침 후보 이벤트 | 회/일 | 0 이상 정수 |
| ambient_temp_c | 돈방 온도 | °C | 현장 범위 확인 |
| humidity_pct | 상대습도 | % | 0~100 |
| camera_coverage_pct | 유효 관찰시간 비율 | % | 0~100 |
| vitality_score | 교육용 복합 활력도 | 0~100 | 임상검증 지표 아님 |
| valid | 현장 QC 통과 여부 | True, False | False 사유 확인 |
| qc_note | QC 사유 | 문자열 | 빈 값은 명시 사유 없음 |

## disease_events.csv

| 열 | 의미 | 비고 |
|---|---|---|
| event_id | 이벤트 ID | 이벤트당 고유 |
| pig_id | 개체 ID | metadata와 결합 |
| clinical_onset_date | 교육용 임상발현일 | 예측 라벨 기준일 |
| confirmation_date | 수의사 확인일 | 실제 발현보다 늦을 수 있음 |
| syndrome | 증후군 분류 | respiratory, enteric, lameness |
| severity | 중증도 | mild, moderate, severe |
| confirmed_by_veterinarian | 수의사 확인 여부 | 합성자료에서는 True |
| treatment_date | 처치 시작일 | 예측변수 사용 금지 |
| recovery_date | 회복 기록일 | 예측변수 사용 금지 |

## practice_dataset.csv 추가 열

| 열 | 의미 | 누수 주의 |
|---|---|---|
| prior_vitality_median_3d | 관찰일 이전 최대 3일 활력도 중앙값 | 현재·미래값 미사용 |
| vitality_delta_3d | 현재 활력도 - 이전 3일 중앙값 | 음수일수록 저하 |
| prior_activity_median_3d | 이전 최대 3일 활동시간 중앙값 | shift 후 계산 |
| activity_delta_pct_3d | 이전 기준선 대비 활동량 변화율 | % |
| cough_events_prior_3d | 이전 최대 3일 기침 이벤트 합 | 당일 제외 |
| study_day | 연구 시작 후 경과일 | 0~41 |
| split | 시간순 자료구분 | train, validation, test |
| disease_next_3d | 향후 1~3일 내 발현 라벨 | 목표변수, 입력 금지 |

## 의도적으로 포함한 품질 문제

- 완전 중복 5행
- 명시적 범위 오류 3행
- 영상 품질 저하에 따른 일부 결측
- 카메라 커버리지 70% 미만 행
- 질병과 무관한 고온·다습 기간의 활동 저하

정확한 개수는 `dataset_summary.json` 및 학생의 코드로 확인한다.

