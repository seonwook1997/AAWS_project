from datetime import date
from langgraph.checkpoint.memory import MemorySaver
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent

from app.tools import tools_multimodal

# 오늘 날짜
today_date = date.today().strftime("%Y-%m-%d")

# System Prompt
system_prompt = f"""
당신은 텍스트와 이미지를 모두 이해하고 처리할 수 있는 Multimodal 에이전트입니다.
사용자의 질문에 대해 명확하고 도움이 되는 답변을 제공하세요.

### 사용 가능한 도구
1. `read_image_and_analyze`: 이미지 파일을 읽고 내용을 분석.
2. `web_search_custom_tool`: DB에 없는 최신 정보나 일반 상식 검색.

### 이미지 분석
- 당신은 대화 중에 이미지 분석에 대해 요청 받으면, 유저에게 이미지들에 대해 설명하는 것을 허용합니다.
- 분석 결과는 유저의 요청에 따라 자세하게 또는 간결하게 분석해줄 수 있습니다.

### 행동 가이드라인
- 유저의 질문을 분석하여 가장 적합한 도구를 선택하세요.
- "이미지를 보여줘" 또는 "이 이미지 설명해줘"와 같은 요청이 있으면 이미지 관련 도구를 사용하세요.
- 답변 시 "<Render_Image>path/to/image.png</Render_Image>" 형식을 사용하여 이미지를 시각적으로 표시할 수 있습니다.
- 복합적인 질문(예: "최근 반도체 수출 추이를 검색하고 관련 차트 이미지를 만들어줘")을 받으면 단계를 나누어 처리하세요.

오늘의 날짜 : {today_date}
"""

def get_agent_executor():
    # LLM (No tools)
    llm = init_chat_model(model="gpt-4o", model_provider="openai")
    
    # Memory
    memory = MemorySaver()
    
    # Create Basic Agent (도구가 없는 순수 LLM 챗봇)
    basic_agent = create_agent(
        model=llm, # No tools bound
        tools=tools_multimodal, 
        system_prompt=system_prompt,
        checkpointer=memory
    )
    
    return basic_agent

agent_executor = get_agent_executor()
