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
st.sidebar.title("Settings")

# OpenAI API Key input
def update_openai_api_key(key: str):
    print(f"Updating OpenAI API Key to '{key[:4]}{'*' * (len(key) - 8)}{key[-4:]}'")
    st.session_state.config.OPENAI_API_KEY = key
    os.environ.update({"OPENAI_API_KEY": key})
api_key = st.sidebar.text_input("Enter OpenAI API Key",
                                value=st.session_state.config.OPENAI_API_KEY,
                                type="password")
if api_key != st.session_state.config.OPENAI_API_KEY:
    update_openai_api_key(api_key)

# LLM Model selection
def update_llm_model(model: str):
    print(f"Updating LLM Model to '{model}'")
    st.session_state.config.LLM_MODEL = model
models = ["fake_gpt", "gpt-4o-mini", "gpt-4o-2024-08-06"]  # Add or modify models as needed
selected_model = st.sidebar.selectbox("Choose LLM Model",
                                      models,
                                      index=models.index(st.session_state.config.LLM_MODEL))
if selected_model != st.session_state.config.LLM_MODEL:
    update_llm_model(selected_model)

# LLM Temperature
def update_llm_temperature(temperature: float):
    print(f"Updating LLM Temperature to {temperature}")
    st.session_state.config.LLM_TEMPERATURE = temperature
temperature = st.sidebar.slider("Choose LLM Temperature",
                                min_value=0.0,
                                max_value=1.0,
                                value=st.session_state.config.LLM_TEMPERATURE,
                                step=0.01)
if temperature != st.session_state.config.LLM_TEMPERATURE:
    update_llm_temperature(temperature)

# Retrieval method selection
retrieval_method = st.sidebar.radio(
    "Choose Retrieval Method",
    ("Deep Answer", "Simple Answer")
)

# top_k selection
top_k = st.sidebar.number_input("Top K Nodes", value=5, min_value=1, step=1)

# Langsmith Tracing
def update_langsmith_tracing(value: bool):
    print(f"Updating Langsmith Tracing to: {value}")
    os.environ.update({"LANGCHAIN_TRACING_V2": str(value)})
langsmith_tracing_env = bool(os.environ.get("LANGCHAIN_TRACING_V2", False))
langsmith_tracing = st.sidebar.checkbox("Enable Langsmith Tracing",
                                        value=langsmith_tracing_env)
if langsmith_tracing_env != langsmith_tracing:
    update_langsmith_tracing(langsmith_tracing)

# Main content
st.title("Knowledge Nexus")

print("Streamlit app is running")

query = st.text_input("Enter your question:")

if query:
    print(f"Query received: {query}\nRetrieving using chosen mode: {retrieval_method}")
    # Use the selected retrieval method
    if retrieval_method == "Deep Answer":
        result = query_controller.deep_answer_on_graph(query, top_k)
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
        st.write(result["llm_answer"].content)

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
