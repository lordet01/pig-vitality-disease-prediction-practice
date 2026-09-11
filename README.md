# 돼지 활력도 기반 질병 위험 예측 실습 패키지

이 패키지는 대학원생 대상 「AI 활용 Python 연구도구 및 실습」의 종합실습용입니다. 모든 값은 교육 목적으로 생성된 **합성데이터**이며 실제 농장, 개체 또는 임상기록과 관계가 없습니다.

## 연구 질문

> 카메라와 환경센서로 측정한 일별 활력도 변화가 향후 3일 이내 수의사가 확인한 질병 발생 위험을 예측하는가?

본 실습의 출력은 질병 **진단**이 아니라 수의사 확인이 필요한 개체를 우선 선별하는 **조기경보 위험도**입니다.

## 폴더 구조

```text
data/raw/pig_metadata.csv
data/raw/pig_daily_observations.csv
data/raw/disease_events.csv
data/clean/practice_dataset.csv
docs/01_experiment_plan.md
docs/02_data_dictionary.md
docs/03_student_practice_guide.md
docs/04_AI_research_ethics_checklist.md
docs/05_ai_prompt_template.md
src/practice_start.py
src/solution_reference.py
results/
dataset_summary.json
requirements.txt
```

## 빠른 시작

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
python src/practice_start.py
```

강사용 참고 결과를 생성하려면 다음을 실행합니다.

```bash
python src/solution_reference.py
```

## 학생 제출물

1. 데이터 품질 보고 4문장
2. 분석대상 선정 흐름도 또는 행 수 표
3. 기초모델과 활력도 변화모델의 검증 성능표
4. 그림 1개 이상
5. 결론 4문장: 데이터, 결과, 활용, 한계
6. AI 사용기록표

## 주의

- `disease_next_3d`는 수의사 확인 이벤트에서 역산한 교육용 라벨입니다.
- 양성률이 낮으므로 정확도만 보고 모델을 평가하지 않습니다.
- 동일 개체의 여러 날짜가 존재합니다. 임의 행 분할은 데이터 누수를 만들 수 있습니다.
- 실제 현장 적용 전에는 외부 농장 검증, 라벨 정확성 검토, 비용-민감도 분석이 필요합니다.

