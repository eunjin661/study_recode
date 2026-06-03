from rag_core import setup_environment
from rag_graph import build_internal_rag_graph, run_graph_question


def main() -> None:
    setup_environment()
    graph = build_internal_rag_graph()

    query = input("질문을 입력하세요: ").strip()

    if not query:
        print("질문이 비어 있습니다.")
        return

    response = run_graph_question(query, graph=graph)

    print("\n답변")
    print("=" * 60)
    print(response["answer"])

    print("\n참고 문서")
    print("=" * 60)
    if response["sources"]:
        for source in response["sources"]:
            print(f"- {source}")
    else:
        print("- 없음")

    print("\n검색 상세")
    print("=" * 60)
    for index, (doc, score) in enumerate(response["results"], start=1):
        print(f"[{index}] {doc.metadata.get('source', 'unknown')} / score={score}")


if __name__ == "__main__":
    main()
