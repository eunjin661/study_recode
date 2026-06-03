from pathlib import Path

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI, OpenAIEmbeddings


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHROMA_DIR = PROJECT_ROOT / "chroma_db"
COLLECTION_NAME = "internal_policy"
EMBEDDING_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4.1-mini"

SYSTEM_PROMPT = """
너는 내부 규정 문서 기반 질의응답 assistant다.

규칙:
1. 반드시 제공된 context만 근거로 답변한다.
2. context에 근거가 없으면 "내부문서에서 확인되지 않습니다."라고 답한다.
3. 답변은 간결하게 작성한다.
4. 참고 문서 목록은 작성하지 않는다.
"""


def setup_environment() -> None:
    load_dotenv(PROJECT_ROOT / ".env")


def create_vectorstore() -> Chroma:
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)

    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(CHROMA_DIR),
    )


def create_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=CHAT_MODEL,
        temperature=0,
    )


def filter_relevant_results(results, max_results=3, max_score_gap=0.25):
    if not results:
        return []

    best_score = results[0][1]

    filtered = []
    for doc, score in results:
        if len(filtered) >= max_results:
            break

        if score <= best_score + max_score_gap:
            filtered.append((doc, score))

    return filtered


def search_documents(vectorstore, query, candidate_count=5, max_results=3):
    raw_results = vectorstore.similarity_search_with_score(query, k=candidate_count)
    return filter_relevant_results(raw_results, max_results=max_results)


def format_context(results) -> str:
    context_blocks = []

    for index, (doc, score) in enumerate(results, start=1):
        source = doc.metadata.get("source", "unknown")

        context_blocks.append(
            f"[문서 {index}]\n"
            f"source: {source}\n"
            f"score: {score}\n"
            f"content:\n{doc.page_content}"
        )

    return "\n\n".join(context_blocks)


def get_sources(results) -> list[str]:
    sources = []

    for doc, _score in results:
        source = doc.metadata.get("source", "unknown")
        if source not in sources:
            sources.append(source)

    return sources


def answer_question(query, vectorstore=None, llm=None):
    if vectorstore is None:
        vectorstore = create_vectorstore()

    if llm is None:
        llm = create_llm()

    results = search_documents(vectorstore, query)
    context = format_context(results)

    user_prompt = f"""
질문:
{query}

context:
{context}
"""

    response = llm.invoke(
        [
            ("system", SYSTEM_PROMPT),
            ("user", user_prompt),
        ]
    )

    answer = response.content.strip()
    is_not_found = "내부문서에서 확인되지 않습니다" in answer
    sources = [] if is_not_found else get_sources(results)

    return {
        "answer": answer,
        "sources": sources,
        "results": results,
    }
