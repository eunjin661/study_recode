from rag_core import answer_question, setup_environment


def main() -> None:
    setup_environment()

    query = input("질문을 입력하세요: ").strip()

    if not query:
        print("질문이 비어 있습니다.")
        return

    response = answer_question(query)

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
