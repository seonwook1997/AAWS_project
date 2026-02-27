from langchain.tools import tool, ToolRuntime
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage

# 기존 워커 에이전트 가져오기
from app.agents.navigator_agent import agent_executor as navigator_agent
from app.agents.coder_agent import agent_executor as coder_agent


# ==========================================
# 1. Worker-as-Tool 도구 정의
# ==========================================
@tool("delegate_navigator", description="사용자 요청을 받아 Navigator에게 Blueprint 생성을 위임합니다.")
def delegate_navigator(user_query: str, runtime: ToolRuntime) -> str:
    # 최신 사용자 메시지를 찾아서 내용을 활용
    original_user_message = next(
        m for m in reversed(runtime.state["messages"])
        if m.type == "human"
    )
    prompt = (
        "다음은 사용자의 원래 요청입니다:\n\n"
        f"{original_user_message.content}\n\n"
        "이 요청에 적합한 웹 크롤링 Blueprint(JSON)를 생성해 주세요."
    )

    # Navigator 에이전트에 전달하고 결과를 받아옴
    result = navigator_agent.invoke({"messages": [HumanMessage(content=prompt)]})
    return result["messages"][-1].content


@tool("delegate_coder", description="Navigator Blueprint를 받아 실제 수집 코드를 작성/실행하도록 Coder에게 위임합니다.")
def delegate_coder(blueprint: str, runtime: ToolRuntime) -> str:
    prompt = (
        "다음은 크롤링을 수행하기 위한 Blueprint입니다:\n\n"
        f"{blueprint}\n\n"
        "이 Blueprint를 토대로 파이썬(Playwright 등) 코드를 작성하고 실행하여, 결과 JSON을 반환하거나 파일로 저장하세요. "
        "파일은 항상 `/workspaces/AAWS_project/code_artifacts` 폴더에 저장하도록 하세요."
    )

    result = coder_agent.invoke({"messages": [HumanMessage(content=prompt)]})
    return result["messages"][-1].content


# ==========================================
# 2. Supervisor 에이전트 정의
# ==========================================
def get_agent_executor():
    llm = init_chat_model(model="gpt-4o-mini", model_provider="openai", temperature=0.2)

    system_prompt = (
        "당신은 웹 데이터 수집 팀의 슈퍼바이저입니다.\n"
        "- 사용자가 웹 크롤링 목표를 제시하면 먼저 `delegate_navigator` 도구를 호출하여 Blueprint를 생성합니다.\n"
        "- 생성된 Blueprint를 받아 `delegate_coder` 도구로 전달해 실제 수집을 수행합니다.\n"
        "- 직접 코드를 작성하거나 작업을 수행하지 말고, 반드시 도구를 이용해 처리하세요.\n"
        "- 각 도구는 한 번씩만 호출하며, 마지막에는 최종 결과를 사용자에게 보고합니다."
    )

    supervisor = create_agent(
        model=llm,
        tools=[delegate_navigator, delegate_coder],
        system_prompt=system_prompt,
        name="supervisor",
    )

    return supervisor


agent_executor = get_agent_executor()
