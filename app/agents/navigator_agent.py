from datetime import date
from langgraph.checkpoint.memory import MemorySaver
from langchain.chat_models import init_chat_model
from app.utils.model_utils import create_chat_model
from langchain.agents import create_agent

from app.tools import tools_navigator

# 오늘 날짜
today_date = date.today().strftime("%Y-%m-%d")

# System Prompt
system_prompt = f"""
당신은 웹사이트의 구조를 분석하고 데이터 수집 전략을 수립하는 '웹 네비게이터'입니다.

[역할 및 지침]
1. 사용자의 요청 또는 Supervisor의 지시에 따라 대상 웹사이트를 탐색합니다.
2. 웹사이트의 구조, 데이터 위치, 페이지네이션, 동적/정적 특성을 파악합니다.
3. 수집할 데이터의 형식(예: 텍스트, 숫자, 이미지 URL 등)과 추출 방식을 분석합니다.
4. 최종적으로 다음과 같은 구조의 JSON Blueprint를 생성합니다:

{{
  "target_url": "수집 대상 URL",
  "description": "이 작업의 목적과 설명",
  "data_fields": ["필드1", "필드2", ...],
  "page_handling": "단일 페이지 또는 다중 페이지 / 페이지네이션 방식",
  "element_selectors": 
  {{
    "필드1": "CSS 또는 XPath 선택자",
    "필드2": "CSS 또는 XPath 선택자"
  }},
  "special_handling": "JavaScript 렌더링 필요 여부, 로그인 필요 여부 등"
}}

5. Blueprint는 Coder가 즉시 구현할 수 있을 정도로 명확하고 완전해야 합니다.
6. 코드를 작성하지 말고, ONLY 분석과 Blueprint 생성에만 집중하세요.

오늘의 날짜: {today_date}
"""

def get_agent_executor():
    # LLM (No tools)
    # choose appropriate LLM; this will pick gpt-4o-mini by default or
    # fall back to google_genai:gemini-flash-latest if the OpenAI model fails.
    llm = create_chat_model()
    
    # Memory
    memory = MemorySaver()
    
    # Create Basic Agent (도구가 없는 순수 LLM 챗봇)
    basic_agent = create_agent(
        model=llm, # No tools bound
        tools=tools_navigator, 
        system_prompt=system_prompt,
        checkpointer=memory
    )
    
    return basic_agent

agent_executor = get_agent_executor()