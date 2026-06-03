import asyncio
import sys
import json
import os
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv(override=True)

# ── OpenAI 클라이언트 ──────────────────────────────────────────────────────────
openai_client = AsyncOpenAI()
MODEL = "gpt-5.4-nano"


def convert_mcp_tools_to_openai(mcp_tools: list) -> list:
    """MCP Tool 목록을 OpenAI function calling 형식으로 변환합니다."""
    openai_tools = []
    for tool in mcp_tools:
        openai_tools.append({
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description or "",
                "parameters": tool.inputSchema if hasattr(tool, "inputSchema") else {"type": "object", "properties": {}}
            }
        })
    return openai_tools


async def run_agent(session: ClientSession, user_question: str):
    """
    OpenAI GPT가 MCP 도구(get_database_schema, execute_sql_query)를 자율적으로
    호출하여 사용자 질문에 답하는 에이전트 루프.
    """
    # ── 1. 서버에서 Tool 목록 조회 ────────────────────────────────────────────
    tools_response = await session.list_tools()
    mcp_tools = tools_response.tools
    openai_tools = convert_mcp_tools_to_openai(mcp_tools)

    print(f"\n사용 가능한 MCP Tool: {[t['function']['name'] for t in openai_tools]}")

    # ── 2. 초기 메시지 구성 ───────────────────────────────────────────────────
    messages = [
        {
            "role": "system",
            "content": (
                "당신은 데이터베이스 전문가 어시스턴트입니다. "
                "사용자의 질문에 답하기 위해, 먼저 get_database_schema를 호출하여 스키마를 확인한 후, "
                "execute_sql_query를 사용하여 적절한 SELECT SQL 쿼리를 실행하세요. "
                "쿼리 결과를 바탕으로 사용자에게 친절하게 답변하세요."
            )
        },
        {
            "role": "user",
            "content": user_question
        }
    ]

    print(f"\n[질문] {user_question}")
    print("=" * 60)

    # ── 3. 에이전트 루프 (tool_calls가 없을 때까지 반복) ──────────────────────
    while True:
        response = await openai_client.chat.completions.create(
            model=MODEL,
            tools=openai_tools,
            messages=messages
        )

        message = response.choices[0].message
        finish_reason = response.choices[0].finish_reason

        # 응답 메시지를 히스토리에 추가
        messages.append(message)

        # ── 4. finish_reason 확인 ─────────────────────────────────────────────
        if finish_reason == "stop":
            print(f"\n[최종 답변]\n{message.content}")
            break

        elif finish_reason == "tool_calls":
            # ── 5. tool_calls 처리 ────────────────────────────────────────────
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                tool_input = json.loads(tool_call.function.arguments)

                print(f"\n[도구 호출] {tool_name}")
                if tool_input:
                    print(f"  입력: {json.dumps(tool_input, ensure_ascii=False)}")

                # MCP 서버에 Tool 호출
                try:
                    mcp_result = await session.call_tool(tool_name, arguments=tool_input)
                    result_text = mcp_result.content[0].text if mcp_result.content else ""
                    print(f"  결과: {result_text[:200]}{'...' if len(result_text) > 200 else ''}")
                except Exception as e:
                    print(f"  [오류] {e}")
                    result_text = f"오류 발생: {str(e)}"

                # Tool 결과를 메시지에 추가
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result_text
                })

        else:
            print(f"[중단] finish_reason={finish_reason}")
            break


async def main():
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    server_params = StdioServerParameters(
        command=sys.executable,
        args=["db_server.py"],
        env=env
    )

    print("DB 서버에 접속을 시도합니다...")

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("서버와 성공적으로 연결되었습니다.")

            # ── 질문 목록 ─────────────────────────────────────────────────────
            questions = [
                "엔지니어링(Engineering) 부서에서 일하는 직원들 중 가장 급여가 높은 사람의 이름과 급여를 알려주세요.",
                "부서별 평균 급여를 높은 순으로 알려주세요.",
                "전체 직원 수와 직급별 인원을 알려주세요.",
            ]

            for question in questions:
                print("\n" + "=" * 60)
                await run_agent(session, question)


if __name__ == "__main__":
    asyncio.run(main())
