import os
from langchain_core.tools import tool
from browser_use import Agent, Browser, ChatOpenAI

# browser-use의 통계 수집(Telemetry)을 비활성화하여 버그 차단
os.environ["ANONYMIZED_TELEMETRY"] = "false"

# 💡 세션을 유지하는 공유 브라우저 인스턴스
shared_browser = Browser(
    headless=False,
    disable_security=True,
    window_size={'width': 1280, 'height': 720},
    keep_alive=True 
)

# ==========================================
# 💡 통합 웹 탐색 도구 (Universal Browser Tool)
# ==========================================
@tool
async def browse_web(
    instruction: str, 
    return_url_only: bool = False, 
    keep_session_alive: bool = False
) -> str:
    """
    주어진 지시사항에 따라 웹 브라우저를 직접 조작하고 결과를 반환하는 통합 웹 탐색 도구입니다.
    
    Args:
        instruction: 브라우저가 수행해야 할 구체적인 행동 지시문.
        return_url_only: True일 경우, 텍스트 요약 대신 최종적으로 찾은 웹페이지의 정확한 URL만 반환합니다. (특정 상품 링크, 출처 URL 등이 필요할 때 설정)
        keep_session_alive: True일 경우, 창을 닫지 않고 이전 작업의 브라우저 상태(로그인, 열린 탭, 스크롤 등)를 유지하며 탐색합니다. (로그인 후 작업, 연속적인 탐색이 필요할 때 설정)
    """
    print(f"\n🌐 [Universal Browser Tool] 행동 개시: {instruction}")
    print(f"   ┣ 옵션 - URL 모드: {return_url_only} | 세션 유지: {keep_session_alive}")
    
    # 1. URL 모드일 경우 프롬프트 강화
    task = instruction
    if return_url_only:
        task += "\n\n[필수 지침] 작업을 완료한 후, 텍스트 요약이 아닌 '반드시' 최종적으로 찾은 웹페이지의 정확한 URL(또는 요청받은 링크들)만 결과(final_result)로 반환하세요."

    # 2. LLM 초기화
    bu_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)
    
    # 3. 에이전트 설정 (세션 유지 옵션에 따라 브라우저 주입 여부 결정)
    agent_kwargs = {
        "task": task,
        "llm": bu_llm,
    }
    
    if keep_session_alive:
        agent_kwargs["browser"] = shared_browser
        
    # 4. 에이전트 실행
    agent = Agent(**agent_kwargs)
    history = await agent.run(max_steps=10)
    
    result_text = history.final_result()
    
    if not result_text:
        return "브라우저 조작을 완료했으나 명확한 결과를 얻지 못했습니다. 다른 명령으로 재시도해보세요."
        
    return result_text

# 다른 파일에서 이 도구를 쉽게 임포트할 수 있도록 리스트로 묶어줍니다.
tools_navigator = [browse_web]