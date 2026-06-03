from rag_core import create_vectorstore, search_documents, setup_environment


def main() -> None:
    setup_environment()
    vectorstore = create_vectorstore()

    query = input("질문을 입력하세요: ").strip()

    if not query:
        print("질문이 비어 있습니다.")
        return

    results = search_documents(vectorstore, query, candidate_count=5, max_results=3)

    print("\n검색 결과")
    print("=" * 60)

    for index, (doc, score) in enumerate(results, start=1):
        source = doc.metadata.get("source", "unknown")
        content = doc.page_content.replace("\n", " ")

        print(f"\n[{index}] source: {source}")
        print(f"score: {score}")
        print(f"content: {content[:1200]}...")


if __name__ == "__main__":
    main()
