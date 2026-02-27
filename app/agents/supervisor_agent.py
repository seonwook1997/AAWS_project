from langchain.tools import tool, ToolRuntime
from langchain.chat_models import init_chat_model
from app.utils.model_utils import create_chat_model
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
import json

# 기존 워커 에이전트 가져오기
from app.agents.navigator_agent import agent_executor as navigator_agent
from app.agents.coder_agent import agent_executor as coder_agent
from app.agents.analyst_agent import agent_executor as analyst_agent


# ==========================================
# 1. Worker-as-Tool 도구 정의
# ==========================================
@tool("delegate_navigator", description="대상 웹사이트를 분석하고 데이터 수집 strategy를 담은 JSON Blueprint를 생성합니다.")
def delegate_navigator(user_request: str) -> str:
    """
    Navigator 에이전트에게 웹사이트 분석과 Blueprint 생성을 위임합니다.
    
    Args:
        user_request: 사용자의 원본 요청 또는 수집 목표
    
    Returns:
        생성된 Blueprint (JSON 형식)
    """
    prompt = (
        "다음은 웹 데이터 수집 작업의 요청사항입니다:\n\n"
        f"{user_request}\n\n"
        "위 요청에 맞는 웹 크롤링 Blueprint를 JSON 형식으로 생성해 주세요. "
        "Blueprint는 다음 구성요소를 반드시 포함해야 합니다:\n"
        "- target_url: 수집 대상 URL\n"
        "- description: 작업 설명\n"
        "- data_fields: 수집할 필드 목록\n"
        "- element_selectors: CSS/XPath 선택자 매핑\n"
        "- special_handling: 특수 처리 필요 사항\n\n"
        "Blueprint만 출력하고 다른 설명은 하지 마세요."
    )
    
    try:
        result = navigator_agent.invoke({"messages": [HumanMessage(content=prompt)]})
        response = result["messages"][-1].content
        return response
    except Exception as e:
        return f"[Error] Navigator 실행 실패: {str(e)}"


@tool("delegate_coder", description="생성된 Blueprint를 바탕으로 크롤링 코드를 작성하고 실행하여 데이터를 수집합니다.")
def delegate_coder(blueprint: str, user_request: str = "") -> str:
    """
    Coder 에이전트에게 Blueprint 기반 데이터 수집을 위임합니다.
    
    Args:
        blueprint: Navigator가 생성한 JSON Blueprint
        user_request: 추가 맥락 (선택사항)
    
    Returns:
        수집 완료 메시지 및 저장 경로
    """
    prompt = (
        "다음은 크롤링을 수행하기 위한 Blueprint입니다:\n\n"
        f"{blueprint}\n\n"
        "위 Blueprint를 기반으로:\n"
        "1. Playwright를 사용하여 파이썬 크롤러 코드를 작성하세요\n"
        "2. 코드를 실행하여 실제로 데이터를 수집하세요\n"
        "3. 수집된 데이터를 JSON 또는 CSV 파일로 저장하세요\n"
        "4. 저장 경로는 반드시 `/workspaces/AAWS_project/code_artifacts` 폴더로 설정하세요\n\n"
        "작업 완료 후 생성된 파일의 경로와 수집된 데이터 건수를 명시하세요."
    )
    
    try:
        result = coder_agent.invoke({"messages": [HumanMessage(content=prompt)]})
        response = result["messages"][-1].content
        return response
    except Exception as e:
        return f"[Error] Coder 실행 실패: {str(e)}"


@tool("delegate_analyst", description="수집된 데이터를 읽어 분석 및 시각화를 수행합니다.")
def delegate_analyst(data_file_path: str) -> str:
    """
    Analyst 에이전트에게 데이터 분석 및 시각화를 위임합니다.
    
    Args:
        data_file_path: 분석할 데이터 파일의 경로 (예: '/workspaces/AAWS_project/code_artifacts/data.json')
    
    Returns:
        생성된 차트 파일의 경로 및 분석 결과
    """
    prompt = (
        "다음 경로의 데이터 파일을 분석하고 시각화하세요:\n\n"
        f"파일 경로: {data_file_path}\n\n"
        "수행 단계:\n"
        "1. 파일을 읽어 데이터의 형태와 특성을 파악하세요\n"
        "2. 데이터에 적합한 차트(막대 그래프, 선 그래프, 산점도 등)를 선택하세요\n"
        "3. matplotlib/seaborn을 사용하여 차트를 생성하세요\n"
        "4. `plt.savefig('/workspaces/AAWS_project/code_artifacts/chart.png')`로 저장하세요\n"
        "5. 생성된 차트의 경로와 간단한 분석 요약을 제공하세요\n\n"
        "주의: plt.show()는 사용하지 마세요. 반드시 파일로 저장하세요."
    )
    
    try:
        result = analyst_agent.invoke({"messages": [HumanMessage(content=prompt)]})
        response = result["messages"][-1].content
        return response
    except Exception as e:
        return f"[Error] Analyst 실행 실패: {str(e)}"


# ==========================================
# 2. Supervisor 에이전트 정의
# ==========================================
def get_agent_executor():
    llm = create_chat_model(temperature=0.2)

    system_prompt = (
        "당신은 웹 데이터 수집 및 분석 팀의 슈퍼바이저입니다.\n"
        "\n[지시사항]\n"
        "1. 사용자가 웹 크롤링 또는 데이터 분석 목표를 제시하면 다음 순서로 진행합니다:\n"
        "   Step 1: `delegate_navigator` 도구를 호출하여 대상 웹사이트의 구조와 수집 전략을 담은 Blueprint(JSON)를 생성합니다.\n"
        "   Step 2: 생성된 Blueprint를 `delegate_coder` 도구로 전달하여 실제 데이터를 수집하고 파일로 저장하게 합니다.\n"
        "   Step 3: 데이터 수집이 완료되면 `delegate_analyst` 도구를 호출하여 저장된 파일을 읽고 시각화 코드를 작성하여 실행합니다.\n"
        "\n2. 도구 사용 규칙:\n"
        "   - 직접 코드를 작성하지 마세요. 반드시 도구를 통해 처리합니다.\n"
        "   - 각 도구의 출력 결과를 다음 도구의 입력으로 사용합니다.\n"
        "   - Navigator의 결과(Blueprint)를 Coder에게 전달합니다.\n"
        "   - Coder의 결과(데이터 파일 경로)를 Analyst에게 전달합니다.\n"
        "\n3. 작업 완료 후:\n"
        "   - 생성된 모든 파일 목록 (JSON, CSV, PNG 등)\n"
        "   - 각 파일의 저장 경로\n"
        "   - 각 단계의 실행 결과 요약\n"
        "   을 사용자에게 명확하고 구조화되어 보고합니다.\n"
        "\n[팁]\n"
        "- 사용자가 시나리오 4 같은 '데이터 수집 + 시각화'를 요청하면, "
        "  반드시 3 단계 모두를 수행해야 합니다.\n"
        "- 각 단계 사이의 파일 경로를 정확히 추적하세요."
    )

    supervisor = create_agent(
        model=llm,
        tools=[delegate_navigator, delegate_coder, delegate_analyst],
        system_prompt=system_prompt,
        name="supervisor",
    )

    return supervisor


agent_executor = get_agent_executor()
