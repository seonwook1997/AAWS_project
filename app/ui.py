import sys
import os

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import re
import uuid
from app.client import AgentClient

# --- Page Config ---
st.set_page_config(page_title="LLMOps AI Chat", layout="wide")

# --- Initialize Client ---
@st.cache_resource
def get_client():
    return AgentClient(base_url="http://localhost:8000")

client = get_client()

# --- Helpers ---
def render_message_content(content):
    """
    텍스트 내의 <Render_Image> 태그를 파싱하여
    텍스트와 이미지를 순서대로 렌더링합니다.
    """
    # 이미지 태그 패턴: <Render_Image>경로</Render_Image>
    pattern = re.compile(r"<Render_Image>(.*?)</Render_Image>")
    
    # 태그를 기준으로 텍스트를 분할 (split하면 텍스트와 경로가 번갈아 나옴)
    parts = pattern.split(content)
    
    for i, part in enumerate(parts):
        # 짝수 인덱스는 일반 텍스트, 홀수 인덱스는 이미지 경로(그룹 캡처)
        if i % 2 == 0:
            if part.strip():
                st.markdown(part)
        else:
            # 이미지 경로
            image_path = part.strip()
            if os.path.exists(image_path):
                st.image(image_path, caption=os.path.basename(image_path))
            else:
                st.error(f"Image not found: {image_path}")

# --- Initialize Session State ---
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Sidebar ---
with st.sidebar:
    st.title("🤖 LLMOps Chat")
    
    # Agent Selector
    agent_name = st.radio(
        "Select Agent",
        ["basic", "rag-basic", "rag-self-query", "multimodal", "navigator"],
        index=0
    )
    
    st.markdown("---")
    st.caption(f"Thread ID: {st.session_state.thread_id}")
    if st.button("New Chat"):
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()

# --- Main Chat Interface ---
st.subheader(f"Chat with `{agent_name}`")

# 1. Display Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        render_message_content(msg["content"])

# 2. Chat Input
if prompt := st.chat_input("메시지를 입력하세요..."):
    # Add User Message to History
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 3. Agent Response (Streaming)
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        # 👇 디버깅: 서버에서 데이터가 오긴 하는지 확인
        st.toast("서버에 요청을 보냈습니다...", icon="⏳") 
        
        try:
            # A. 텍스트 스트리밍 수신
            for chunk in client.stream(agent_name, prompt, st.session_state.thread_id):
                
                # 🚨 핵심 디버깅: 터미널 창(VS Code/명령프롬프트)에 실제 청크 데이터 출력
                print("들어온 청크 데이터:", chunk) 
                
                # chunk가 딕셔너리인지, 문자열인지에 따라 다르게 처리해야 할 수 있습니다.
                if isinstance(chunk, dict):
                    # 현재 코드의 로직 (chunk["type"] == "token" 등을 기대함)
                    if "type" in chunk:
                        if chunk["type"] == "token":
                            content = chunk.get("content", "")
                            full_response += content
                            message_placeholder.markdown(full_response + "▌")
                        elif chunk["type"] == "tool_start":
                            with st.status(f"🛠️ 도구 사용 중: {chunk.get('name', '알 수 없음')}", expanded=False) as status:
                                st.write(f"Input: {chunk.get('input')}")
                                status.update(state="complete")
                        elif chunk["type"] == "error":
                            st.error(f"Error: {chunk.get('content')}")
                elif isinstance(chunk, str):
                    # 만약 서버가 딕셔너리가 아니라 단순 텍스트만 뱉어낸다면?
                    full_response += chunk
                    message_placeholder.markdown(full_response + "▌")

        except Exception as e:
            st.error(f"통신 중 오류 발생: {str(e)}")
        
        # B. 완료 후 최종 렌더링
        message_placeholder.empty() # 스트리밍 효과(▌) 지우기
        
        # 방어 코드: 텍스트가 비어있는지 확인
        if full_response.strip():
            render_message_content(full_response) 
            st.session_state.messages.append({"role": "assistant", "content": full_response})
        else:
            # 화면에 아무것도 안 나오는 원인을 파악하기 위한 경고창
            st.warning("⚠️ 백엔드에서 응답을 받았지만 텍스트가 비어있습니다. 터미널의 '들어온 청크 데이터' 로그를 확인하여 JSON 키값을 맞게 수정하세요.")