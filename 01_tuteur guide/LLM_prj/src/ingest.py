from pathlib import Path

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data" / "internal" / "policy"
CHROMA_DIR = PROJECT_ROOT / "chroma_db"
COLLECTION_NAME = "internal_policy"

EXCLUDE_FILES = {
    "rag_test_questions.txt",
}


def load_policy_documents() -> list[Document]:
    documents = []

    for file_path in sorted(DATA_DIR.glob("*.txt")):
        if file_path.name in EXCLUDE_FILES:
            continue

        text = file_path.read_text(encoding="utf-8")

        documents.append(
            Document(
                page_content=text,
                metadata={
                    "source": file_path.name,
                    "path": str(file_path),
                    "category": "internal_policy",
                },
            )
        )

    return documents


def main() -> None:
    load_dotenv(PROJECT_ROOT / ".env")

    documents = load_policy_documents()

    print(f"Loaded documents: {len(documents)}")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=120,
    )

    chunks = splitter.split_documents(documents)

    print(f"Created chunks: {len(chunks)}")

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        persist_directory=str(CHROMA_DIR),
    )

    print(f"Saved ChromaDB to: {CHROMA_DIR}")
    print(f"Collection name: {COLLECTION_NAME}")


if __name__ == "__main__":
    main()