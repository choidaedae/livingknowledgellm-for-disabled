import json
import argparse
from prometheus_eval.vllm import VLLM
from prometheus_eval import PrometheusEval
from prometheus_eval.prompts import ABSOLUTE_PROMPT, SCORE_RUBRIC_TEMPLATE

# Argument parser 설정
parser = argparse.ArgumentParser(description="Evaluate responses using Prometheus model.")
parser.add_argument(
    "--json_file",
    type=str,
    required=True,
    help="Path to the JSON file containing evaluation data."
)
args = parser.parse_args()

# JSON 파일에서 데이터 로드
with open(args.json_file, "r", encoding="utf-8") as file:
    data = json.load(file)

# 모델 초기화
model = VLLM(model="prometheus-eval/prometheus-7b-v2.0")
judge = PrometheusEval(model=model, absolute_grade_template=ABSOLUTE_PROMPT)

# JSON 데이터에서 변수 설정
instructions = data["instructions"]
responses = data["responses"]
reference_answers = data["reference_answers"] * 4
rubric_data = data["rubric_data"]

# Rubric 데이터 포맷팅
score_rubric = SCORE_RUBRIC_TEMPLATE.format(**rubric_data)

# Batch Evaluation 실행
feedbacks, scores = judge.absolute_grade(
    instructions=instructions,
    responses=responses,
    rubric=score_rubric,
    reference_answers=reference_answers
)

# 결과 출력
print("Evaluation Results:")
for i, (feedback, score) in enumerate(zip(feedbacks, scores), 1):
    print(f"Scenario {i}:")
    print(f"  Feedback: {feedback}")
    print(f"  Score: {score}")
