from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from rag_core import (
    SYSTEM_PROMPT,
    create_llm,
    create_vectorstore,
    format_context,
    get_sources,
    search_documents,
)


class RagState(TypedDict, total=False):
    query: str
    results: list[Any]
    context: str
    route: str
    answer: str
    sources: list[str]
    is_not_found: bool


def build_internal_rag_graph(vectorstore=None, llm=None):
    if vectorstore is None:
        vectorstore = create_vectorstore()

    if llm is None:
        llm = create_llm()

    def retrieve_internal(state: RagState) -> RagState:
        results = search_documents(vectorstore, state["query"])

        return {
            "results": results,
            "context": format_context(results),
        }

    def check_answerable(state: RagState) -> RagState:
        user_prompt = f"""
질문:
{state["query"]}

context:
{state["context"]}

위 context만 사용해서 질문에 직접 답할 수 있는지 판단해라.
반드시 answerable 또는 not_answerable 중 하나만 출력해라.
"""

        response = llm.invoke(
            [
                (
                    "system",
                    "너는 검색된 내부문서 context의 답변 가능 여부만 판단하는 분류기다.",
                ),
                ("user", user_prompt),
            ]
        )

        decision = response.content.strip().lower()

        if "not_answerable" in decision:
            route = "external_needed"
        elif "answerable" in decision:
            route = "generate_answer"
        else:
            route = "external_needed"

        return {"route": route}

    def generate_answer(state: RagState) -> RagState:
        user_prompt = f"""
질문:
{state["query"]}

context:
{state["context"]}
"""

        response = llm.invoke(
            [
                ("system", SYSTEM_PROMPT),
                ("user", user_prompt),
            ]
        )

        answer = response.content.strip()
        is_not_found = "내부문서에서 확인되지 않습니다" in answer
        sources = [] if is_not_found else get_sources(state["results"])

        return {
            "answer": answer,
            "sources": sources,
            "is_not_found": is_not_found,
        }

    def external_needed(state: RagState) -> RagState:
        return {
            "answer": "내부문서에서 확인되지 않습니다. 외부 검색 또는 MCP 호출이 필요합니다.",
            "sources": [],
            "is_not_found": True,
        }

    def route_after_check(state: RagState) -> str:
        return state["route"]

    graph = StateGraph(RagState)
    graph.add_node("retrieve_internal", retrieve_internal)
    graph.add_node("check_answerable", check_answerable)
    graph.add_node("generate_answer", generate_answer)
    graph.add_node("external_needed", external_needed)

    graph.add_edge(START, "retrieve_internal")
    graph.add_edge("retrieve_internal", "check_answerable")
    graph.add_conditional_edges(
        "check_answerable",
        route_after_check,
        {
            "generate_answer": "generate_answer",
            "external_needed": "external_needed",
        },
    )
    graph.add_edge("generate_answer", END)
    graph.add_edge("external_needed", END)

    return graph.compile()


def run_graph_question(query: str, graph=None) -> dict[str, Any]:
    if graph is None:
        graph = build_internal_rag_graph()

    final_state = graph.invoke({"query": query})

    return {
        "answer": final_state["answer"],
        "sources": final_state["sources"],
        "results": final_state["results"],
        "is_not_found": final_state["is_not_found"],
    }
