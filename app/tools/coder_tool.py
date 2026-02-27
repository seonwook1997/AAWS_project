import os
import subprocess
from langchain.tools import tool

# ==========================================
# 1. 🛠️ 파이썬 코드 실행 공간 및 도구 (Tool)
# ==========================================

# 작업 및 실행 파일들이 모일 대상 디렉토리 (없으면 자동 생성)
ARTIFACT_DIR = os.path.join(os.getenv("PROJECT_ROOT", os.getcwd()), "code_artifacts")
os.makedirs(ARTIFACT_DIR, exist_ok=True)

@tool(parse_docstring=True)
def execute_python_code(code: str, filename: str = "generated_script.py") -> str:
    """주어진 파이썬 코드를 로컬 환경의 파일로 저장하고 실행한 뒤, 그 결과(표준 출력 및 에러)를 반환합니다.
    코드가 정상 작동하는지 테스트하고 디버깅할 때 사용하세요.
    
    Args:
        code: 실행할 완전한 파이썬 스크립트 코드 내용 (모든 import 포함 필수).
        filename: 코드를 저장할 파이썬 파일명 (기본값: 'generated_script.py').
    """
    # ✅ 항상 code_artifacts 경로 내부로 저장되도록 경로 강제 처리
    safe_filename = os.path.basename(filename)
    filepath = os.path.join(ARTIFACT_DIR, safe_filename)
    
    print(f"\n🐍 [Coder Tool] '{filepath}' 파일 생성 및 실행 중...")
    
    try:
        # 코드를 파일로 저장 (무조건 덮어쓰기)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(code)
            
        # 파이썬 실행 (작업 디렉토리를 ARTIFACT_DIR 내부로 한정)
        result = subprocess.run(
            ["python", safe_filename], 
            cwd=ARTIFACT_DIR, # ✅ 작업 디렉토리 지정!
            capture_output=True, 
            text=True, 
            timeout=30 # 무한 루프 등 시간끌기 방지
        )
        
        output = result.stdout
        if result.stderr:
            output += f"\n[Error Output]\n{result.stderr}"
            
        if not output.strip():
            output = "[System] 코드가 에러 없이 실행되었으나 출력된 내용이 없습니다."
            
        return output
        
    except subprocess.TimeoutExpired:
        return "[Error] 실행 시간(30초)을 초과했습니다. 무한 루프 수정을 시도하세요."
    except Exception as e:
        return f"[System Error] 코드 실행 오류 발생: {str(e)}"

# 다른 파일에서 이 도구를 쉽게 임포트할 수 있도록 리스트로 묶어줍니다.
tools_coder = [execute_python_code]