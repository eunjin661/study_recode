import streamlit as st

from rag_core import answer_question, create_llm, create_vectorstore, setup_environment


@st.cache_resource
def load_vectorstore():
    return create_vectorstore()


@st.cache_resource
def load_llm():
    return create_llm()


def main():
    setup_environment()

    st.set_page_config(
        page_title="내부 규정 QA",
        page_icon="📚",
        layout="wide",
    )

    st.title("내부 규정 문서 질의응답")
    st.caption("ChromaDB에 저장된 내부 규정 문서를 검색하고, 검색된 근거만 사용해 답변합니다.")

    query = st.text_input(
        "질문",
        placeholder="예: 지각 3번이면 어떻게 처리돼?",
    )

    run_button = st.button("질문하기", type="primary")

    if run_button:
        if not query.strip():
            st.warning("질문을 입력하세요.")
            return

        with st.spinner("내부문서를 검색하고 답변을 생성하는 중입니다."):
            response = answer_question(
                query.strip(),
                vectorstore=load_vectorstore(),
                llm=load_llm(),
            )

        st.subheader("답변")
        st.write(response["answer"])

        st.subheader("참고 문서")
        if response["sources"]:
            for source in response["sources"]:
                st.write(f"- {source}")
        else:
            st.write("- 없음")

        with st.expander("검색 상세"):
            for index, (doc, score) in enumerate(response["results"], start=1):
                st.markdown(f"**[{index}] {doc.metadata.get('source', 'unknown')}**")
                st.write(f"score: {score}")
                st.write(doc.page_content)


if __name__ == "__main__":
    main()
