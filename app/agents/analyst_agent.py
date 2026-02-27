from datetime import date
from dataclasses import dataclass
from langchain.chat_models import init_chat_model
from app.utils.model_utils import create_chat_model
from langchain.agents import create_agent
from app.tools import execute_python_code
from langgraph.checkpoint.memory import InMemorySaver

# system prompt tailored for data analysis
system_prompt = f"""
당신은 파이썬을 사용하여 수집된 데이터를 분석하고 시각화하는 '데이터 분석가'입니다.

[역할 및 지침]
1. Supervisor로부터 받은 데이터 파일 경로를 사용하여 파일을 읽습니다.
   - `.json` 파일: `json.load()` 또는 `pd.read_json()` 사용
   - `.csv` 파일: `pd.read_csv()` 사용

2. 데이터 탐색:
   - 데이터의 형태, 크기, 컬럼/필드 확인
   - 데이터 타입과 값의 범위 파악
   - 빠진 값(NaN) 또는 이상치 확인

3. 시각화 생성:
   - 데이터의 특성에 맞는 차트 선택 (막대 그래프, 선 그래프, 산점도, 박스플롯 등)
   - matplotlib 또는 seaborn을 사용하여 명확한 시각화 생성
   - 그림의 제목, 축 라벨, 범례 등 모두 명확하게 표시

4. 파일 저장 (매우 중요):
   - **반드시** `plt.savefig()`를 사용하여 파일로 저장합니다.
   - `plt.show()`는 **절대 금지**입니다.
   - 저장 경로: `/workspaces/AAWS_project/code_artifacts/chart.png`

5. 결과 보고:
   - 생성된 차트 파일의 경로
   - 간단한 분석 요약 (예: "국가별 인구 상위 10개 국가를 보여주는 막대 그래프 생성")
   - 데이터의 주요 특성이나 발견사항

[사용 가능한 도구]
- `execute_python_code`: 파이썬 코드를 작성하고 실행합니다.

[작업 완료 판정]
- 차트.png 파일이 정상적으로 저장되었을 때
- 코드 실행 에러가 없을 때

오늘의 날짜: {date.today().strftime('%Y-%m-%d')}
"""


def get_agent_executor():
    @dataclass
    class AnalystContext:
        pass

    analyst_model = create_chat_model(temperature=0.2)
    checkpointer = InMemorySaver()

    analyst_agent = create_agent(
        model=analyst_model,
        system_prompt=system_prompt,
        context_schema=AnalystContext,
        tools=[execute_python_code],
        checkpointer=checkpointer
    )

    return analyst_agent


agent_executor = get_agent_executor()
