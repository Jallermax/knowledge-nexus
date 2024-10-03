import os

import streamlit as st
import streamlit.components.v1 as components

from graph_rag.config.config_manager import default_config
from graph_rag.controller import query_controller
from graph_rag.storage import Neo4jManager

neo4j_manager = Neo4jManager()

# Initialize session state
if 'config' not in st.session_state:
    st.session_state.config = default_config
if 'use_cache' not in st.session_state:
    st.session_state.use_cache = True

st.set_page_config(page_title="Knowledge Nexus - Graph-based Q&A", layout="wide")

# Custom CSS for styling
st.markdown("""
<style>
    .thinking-pane {
        background-color: #f0f0f0;
        border-radius: 5px;
        padding: 10px;
        margin-top: 20px;
    }
    .stJson {
        max-height: 300px;
        overflow-y: auto;
    }
    .graph-pane {
        height: calc(100vh - 100px);
        overflow-y: auto;
    }
    .scrollable-text {
        max-height: 300px;
        overflow-y: auto;
        border: 1px solid #e0e0e0;
        padding: 10px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar for settings
with st.sidebar:
    st.title("Settings")
    with st.form("Settings form"):
        # OpenAI API Key input
        def mask_key(key: str):
            return f"{key[:4]}{'*' * (len(key) - 8)}{key[-4:]}"
        def update_openai_api_key(key: str):
            print(f"Updating OpenAI API Key to '{mask_key(key)}'")
            st.session_state.config.OPENAI_API_KEY = key
            os.environ.update({"OPENAI_API_KEY": key})
        api_key = st.text_input("Enter OpenAI API Key",
                                        value=mask_key(st.session_state.config.OPENAI_API_KEY),
                                        type="password")
        if api_key != mask_key(st.session_state.config.OPENAI_API_KEY) and api_key != st.session_state.config.OPENAI_API_KEY:
            update_openai_api_key(api_key)

        # LLM Model selection
        def update_llm_model(model: str):
            print(f"Updating LLM Model to '{model}'")
            st.session_state.config.LLM_MODEL = model
        models = ["fake_gpt", "gpt-4o-mini", "gpt-4o-2024-08-06"]  # Add or modify models as needed
        selected_model = st.selectbox("Choose LLM Model",
                                              models,
                                              index=models.index(st.session_state.config.LLM_MODEL))
        if selected_model != st.session_state.config.LLM_MODEL:
            update_llm_model(selected_model)

        # LLM Temperature
        def update_llm_temperature(temp: float):
            print(f"Updating LLM Temperature to {temp}")
            st.session_state.config.LLM_TEMPERATURE = temp
        temperature = st.slider("Choose LLM Temperature",
                                        min_value=0.0,
                                        max_value=1.0,
                                        value=st.session_state.config.LLM_TEMPERATURE,
                                        step=0.01)
        if temperature != st.session_state.config.LLM_TEMPERATURE:
            update_llm_temperature(temperature)

        # Retrieval method selection
        retrieval_method = st.radio(
            "Choose Retrieval Method",
            ("Deep Answer", "Simple Answer")
        )

        # top_k selection
        top_k = st.number_input("Top K Nodes", value=5, min_value=1, step=1)

        # Langsmith Tracing
        def update_langsmith_tracing(value: bool):
            print(f"Updating Langsmith Tracing to: {value}")
            os.environ.update({"LANGCHAIN_TRACING_V2": str(value)})
        langsmith_tracing_env = bool(os.environ.get("LANGCHAIN_TRACING_V2", False))
        langsmith_tracing = st.toggle("Enable Langsmith Tracing",
                                                value=langsmith_tracing_env)
        if langsmith_tracing_env != langsmith_tracing:
            update_langsmith_tracing(langsmith_tracing)

        use_cache = st.toggle("Use cache", key="use_cache",
                              help="Toggles caching of LLM responses and graph data.")

        st.form_submit_button("Apply Settings", type="secondary")

@st.cache_resource
def perform_rag(q: str, k: int, key2, key3, key4):
    return query_controller.deep_answer_on_graph(q, k)


# Main content
st.title("Knowledge Nexus")

print("Streamlit app is running")

with st.form("my_form"):

    query = st.text_area("Enter your question:", placeholder="What are my main goals?")

    submitted = st.form_submit_button("Submit")

    if not api_key.startswith("sk-"):
        st.warning("Please enter your OpenAI API key!", icon="⚠")
    elif query and submitted and api_key.startswith("sk-"):
        print(f"Query received: {query}\nRetrieving using chosen mode: {retrieval_method}")
        st.spinner(text="LLM is thinking...")
        # Use the selected retrieval method
        if retrieval_method == "Deep Answer":
            result = perform_rag(query, top_k, api_key, selected_model, temperature) if st.session_state.use_cache \
                else query_controller.deep_answer_on_graph(query, top_k)
        else:
            result = query_controller.answer_on_graph(query)

        # Create two columns
        col1, col2 = st.columns([3, 2])

        with col1:
            # Thinking section with toggle
            with st.expander("Thinking", expanded=False):
                st.markdown('<div class="thinking-pane">', unsafe_allow_html=True)

                # LLM context
                st.subheader("LLM answer metadata:")
                st.json(result['llm_answer'].response_metadata)

                # Intermediate steps
                st.subheader("Intermediate Steps:")
                st.markdown('<div class="scrollable-text">', unsafe_allow_html=True)
                for step in result.get('intermediate_steps', []):
                    st.text(step)
                st.markdown('</div>', unsafe_allow_html=True)

                # Graph data
                st.subheader("Graph Data:")
                st.json(result["graph_data"])

                st.markdown('</div>', unsafe_allow_html=True)

            st.subheader("Answer:")
            st.info(result["llm_answer"].content)
            st.feedback("thumbs")

        with col2:
            st.subheader("Graph Visualization:")
            with st.container():
                st.markdown('<div class="graph-pane">', unsafe_allow_html=True)
                graph_html = query_controller.render_graph(result["graph_data"])
                components.html(open(graph_html, 'r').read(), height=600)
                st.markdown('</div>', unsafe_allow_html=True)

    else:
        st.write("Please enter a question to get started.")

print("Streamlit app script completed")
