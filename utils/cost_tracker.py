import json
import os
from datetime import datetime

class CostTracker:
    def __init__(self, log_file: str = "agent_cost_log.json"):
        self.log_file = log_file
        # 파일이 없으면 초기화
        if not os.path.exists(self.log_file):
            with open(self.log_file, "w", encoding="utf-8") as f:
                json.dump({"total_accumulated_cost": 0.0, "runs": []}, f, indent=4)

    def record_usage(self, task_name: str, usage_summary):
        """
        주어진 사용량(UsageSummary) 객체를 받아 파일에 누적 기록합니다.
        """
        if not usage_summary or not hasattr(usage_summary, "total_cost"):
            return

        # 기존 로그 읽기
        with open(self.log_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        cost = usage_summary.total_cost
        tokens = usage_summary.total_tokens

        # 새 실행 기록 생성
        run_record = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "task_name": task_name,
            "tokens": tokens,
            "cost": cost
        }

        # 데이터 업데이트
        data["runs"].append(run_record)
        data["total_accumulated_cost"] += cost

        # 파일에 다시 쓰기
        with open(self.log_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        print(f"💰 [비용 기록 완료] 이번 작업({task_name}): ${cost:.4f} / 누적 총액: ${data['total_accumulated_cost']:.4f}")

# === 사용 예시 ===
if __name__ == "__main__":
    from browser_use import Agent, ChatGoogle
    from dotenv import load_dotenv
    import asyncio
    import nest_asyncio
    
    nest_asyncio.apply()
    load_dotenv()
    
    async def sample_run():
        tracker = CostTracker()
        llm = ChatGoogle(model="gemini-flash-latest")
        
        # 첫 번째 작업
        task1 = "네이버 메인에 접속해줘"
        agent1 = Agent(task=task1, llm=llm, calculate_cost=True)
        history1 = await agent1.run(max_steps=2)
        tracker.record_usage(task1, history1.usage)
        
        # 두 번째 작업
        task2 = "구글 메인에 접속해줘"
        agent2 = Agent(task=task2, llm=llm, calculate_cost=True)
        history2 = await agent2.run(max_steps=2)
        tracker.record_usage(task2, history2.usage)
        
    asyncio.run(sample_run())
