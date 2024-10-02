import json
import tempfile
from typing import Dict, Any, Optional, List

from langchain.chains.base import Chain
from langchain_community.chains.graph_qa.cypher import GraphCypherQAChain
from langchain_community.chains.graph_qa.prompts import (
    CYPHER_QA_PROMPT,
)
from langchain_core.callbacks import CallbackManagerForChainRun, StdOutCallbackHandler
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableParallel
from langchain_core.runnables.config import RunnableConfig
from langchain_openai import ChatOpenAI
from pyvis.network import Network

from graph_rag.config.config_manager import default_config
from graph_rag.processor import ContentChunkerAndEmbedder
from graph_rag.storage import Neo4jManager

CYPHER_GENERATION_TEMPLATE = """Task:Generate Cypher statement to query a graph database.
Instructions:
Use only the provided relationship types and properties in the schema.
Do not use any other relationship types or properties that are not provided.
Always exclude 'embedding' property of the nodes as they are not relevant to the query.
Always create a refined graph query that retrieves only the necessary nodes and relationships.
Never generate a Cypher statement Matching all of the nodes in the graph.
Schema:
{schema}
Note: Do not include any explanations or apologies in your responses.
Do not respond to any questions that might ask anything else than for you to construct a Cypher statement.
Do not include any text except the generated Cypher statement.

The question is:
{question}"""
CYPHER_GENERATION_PROMPT = PromptTemplate(
    input_variables=["schema", "question"], template=CYPHER_GENERATION_TEMPLATE
)
graph_manager = Neo4jManager()


class GraphRetriever(Chain):
    input_key: str = "question"  #: :meta private:
    output_key: str = "context"  #: :meta private:
    return_full_graph: bool = False
    top_k: int = 10

    @property
    def input_keys(self) -> List[str]:
        """Input keys.

        :meta private:
        """
        return [self.input_key]

    @property
    def output_keys(self) -> List[str]:
        """Output keys.

        :meta private:
        """
        _output_keys = [self.output_key]
        if self.return_full_graph:
            _output_keys += ["full_graph_result"]
        return _output_keys

    def _call(self, inputs: Dict[str, Any],
              run_manager: Optional[CallbackManagerForChainRun] = None) -> Dict[str, Any]:

        _embedder = ContentChunkerAndEmbedder()
        _graph_manager = Neo4jManager()
        _run_manager = run_manager or CallbackManagerForChainRun.get_noop_manager()
        question = inputs[self.input_key]
        _run_manager.on_text("Question for similarity search on graph:", end="\n", verbose=True)
        _run_manager.on_text(str(question), color="green", end="\n", verbose=True)
        embed_query = _embedder.embeddings.embed_query(question)
        result = _graph_manager.retriever.get_enhanced_visualization_data(embed_query)
        final_result = []
        if result and result["nodes"] and result["relationships"]:
            unique_nodes = list({item['id']: item for item in result["nodes"]}.values())
            result["nodes"] = sorted(unique_nodes, key=lambda n: n["similarity"], reverse=True)[:self.top_k]
            node_ids = [node['id'] for node in result["nodes"]]
            result["relationships"] = [rel for rel in result["relationships"]
                                       if rel["source_id"] in node_ids and rel["target_id"] in node_ids]
            final_result = [{"title": node["title"], "content": node["content"]}
                            for node in result["nodes"] if node["content"]]
        _run_manager.on_text("Got result:", end="\n", verbose=True)
        _run_manager.on_text(str(result), color="green", end="\n", verbose=True)

        _run_manager.on_text("Final result:", end="\n", verbose=True)
        _run_manager.on_text(str(final_result), color="green", end="\n", verbose=True)
        response = {self.output_key: final_result, "question": question}
        if self.return_full_graph:
            response.update({"full_graph_result": result})
        return response


def answer_on_graph(query):
    llm = ChatOpenAI(
        temperature=default_config.LLM_TEMPERATURE,
        api_key=default_config.OPENAI_API_KEY,
        model=default_config.LLM_MODEL
    )
    search_by_schema_chain = CYPHER_GENERATION_PROMPT | llm
    invoke_cypher_qna(llm, query, search_by_schema_chain)


def deep_answer_on_graph(query, top_k=5):
    llm = ChatOpenAI(
        temperature=default_config.LLM_TEMPERATURE,
        api_key=default_config.OPENAI_API_KEY,
        model=default_config.LLM_MODEL
    )
    runnable_cfg = RunnableConfig(callbacks=[StdOutCallbackHandler()])
    semantic_retrieval = GraphRetriever(top_k=top_k, return_full_graph=True)

    chain = (semantic_retrieval
             | RunnableParallel(
                llm_answer=CYPHER_QA_PROMPT | llm,
                graph_data=lambda x: x["full_graph_result"]
            ))

    # TODO: Compare and evaluate semantic score on the big chunks (page or 2000 words) vs smaller chunks (RAPTOR semantic meaning or markdown headers/blocks)
    result = chain.invoke({"question": query}, config=runnable_cfg)

    # Process LLM response
    print(f"Final answer: {result['llm_answer'].content}")
    print(f"Metadata: {result['llm_answer'].response_metadata}")

    return result


def render_graph(graph_data):
    net = Network(height="500px", width="100%", bgcolor="#222222", font_color="white")

    for node in graph_data["nodes"]:
        color = "#ff0000" if node["highlighted"] else "#ffffff"
        size = 30 if node["highlighted"] else 20
        net.add_node(node["id"], label=node["title"], title=f"{node['type']}: {node['content']}",
                     color=color, size=size)

    for edge in graph_data["relationships"]:
        net.add_edge(edge["source_id"], edge["target_id"], title=edge["type"])

    # Generate HTML file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as tmpfile:
        net.save_graph(tmpfile.name)
        return tmpfile.name


def invoke_cypher_qna(llm, query, cypher_generation_chain):
    chain = GraphCypherQAChain.from_llm(llm=llm,
                                        graph=graph_manager.graph,
                                        # cypher_prompt=CYPHER_GENERATION_PROMPT,
                                        cypher_generation_chain=cypher_generation_chain,
                                        validate_cypher=True,
                                        verbose=True,
                                        use_function_response=True,
                                        return_intermediate_steps=True)
    result = chain.invoke({"query": query})
    print(f"Intermediate steps: {result['intermediate_steps']}")
    print(f"Final answer: {result['result']}")


if __name__ == '__main__':
    query = "List my most important projects that align with my values and goals"
    # answer_on_graph(query)
    deep_answer_on_graph(query)
