from datetime import datetime

import streamlit as st

def about():
    st.title("📚 Local RAG")
    st.caption(
        f"Developed by Jon Fairbanks &copy; {datetime.now().year}"
    )
    st.write("")

    st.subheader("Links")
    st.markdown(
        """
        * [GitHub](https://github.com/jonfairbanks/local-rag)
        * [Docker Hub](#)
    """
    )

    st.subheader("Resources")
    st.markdown(
        """
        * [What is RAG?](https://blogs.nvidia.com/blog/what-is-retrieval-augmented-generation/)
        * [What are embeddings?](https://aws.amazon.com/what-is/embeddings-in-machine-learning/)
        * [Embeddings Leaderboard](https://huggingface.co/spaces/mteb/leaderboard)
    """
    )

    st.subheader("Help")
    st.markdown(
        """
        * [Bug Reports](https://github.com/jonfairbanks/local-rag/issues)
        * [Feature Requests](https://github.com/jonfairbanks/local-rag/discussions/new?category=ideas)
    """
    )