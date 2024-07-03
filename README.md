# Knowledge Nexus: Your AI-Powered Personal Knowledge Discovery Engine

## 🌟 Project Overview

Knowledge Nexus is an advanced personal knowledge management system that transforms the way individuals organize, process, and discover insights from their digital content. By leveraging the power of AI and graph databases, this project addresses the challenge of information overload and disconnected data silos that many knowledge workers face in today's digital landscape.

Unlike traditional note-taking or knowledge management tools that rely heavily on manual organization, Knowledge Nexus automates the process of extracting key concepts, generating insights, and creating meaningful connections across your personal knowledge base.

## 🎯 Key Challenges Addressed

1. **Information Overload**: Knowledge Nexus cuts through the noise by automatically extracting key entities and insights from various content sources, helping you focus on what's important.

2. **Manual Processing Overhead**: Traditional tools require significant manual effort to organize and connect information. Knowledge Nexus automates this process, saving you time and cognitive effort.

3. **Limited Contextual Understanding**: While tools like Obsidian or Roam Research rely on explicit links, Knowledge Nexus uses AI to understand semantic and topical relationships, creating a richer, more nuanced knowledge graph.

4. **Disconnected Data Silos**: By importing and processing data from various sources into a single, interconnected knowledge graph, Knowledge Nexus bridges the gaps between your different information repositories.

5. **Difficulty in Discovering New Connections**: The AI-powered system can uncover non-obvious relationships between different pieces of information, potentially leading to new insights or ideas that you might have missed.

## 🚀 Key Features

- **Multi-Source Data Integration**: Import content from Notion, Pocket, web pages, and more (extensible architecture for adding new sources).
- **AI-Powered Entity and Topic Extraction**: Automatically identify and extract key entities and topics from processed content.
- **Intelligent Insight Generation**: Leverage AI to generate concise insights from your personal knowledge base.
- **Semantic Knowledge Graph Construction**: Build a comprehensive, interconnected graph of entities, topics, and content using Neo4j, reflecting not just explicit links but semantic relationships.
- **Contextual Querying and Exploration**: Easily retrieve relevant content and explore connections within your knowledge graph.
- **Personalized Knowledge Assistant**: Tailored to your specific needs and preferences, helping you find tools, frameworks, and best practices aligned with your views.

## 🌈 What Sets Knowledge Nexus Apart

- **Automation with a Personal Touch**: While it automates much of the knowledge processing, Knowledge Nexus is designed to adapt to your unique perspective and needs.
- **Deep Semantic Understanding**: Goes beyond simple keyword matching or explicit links to understand the true context and relationships within your knowledge base.
- **Data under your control**: All your data is stored locally, ensuring that your personal knowledge remains under your control and easily exportable.
- **Low Maintenance, High Value**: Once set up, Knowledge Nexus continually processes and organizes your information with minimal manual intervention, allowing you to focus on generating and using knowledge rather than managing it.

## 👥 Who Is It For?

Knowledge Nexus is primarily designed for individual users who:
- Deal with large amounts of information from various sources
- Seek to uncover new insights and connections within their knowledge base
- Want to reduce the cognitive overhead of manual knowledge management
- Are looking for a personal research assistant to aid in complex tasks or decision-making

## 🛠 Getting Started

1. install neo4j
2. install python
3. make and configure .env in root directory
4. input root `notion_page_id` into `main.py` from where to start the graph
5. `pip install -r requirements.txt`
6. `python main.py`

## 🔮 Future Enhancements

- Enhanced personalization through adaptive learning of user preferences and interests
- Integration with additional productivity tools and data sources
- Advanced visualization options for exploring your knowledge graph

## 🛠️ Technical Highlights

- **LangChain Integration**: Utilize the power of LangChain for advanced NLP tasks and AI agent coordination.
- **Neo4j Graph Database**: Leverage the capabilities of graph databases for efficient storage and querying of interconnected data.
- **Configurable AI Agents**: Customize AI behavior and prompts to suit specific use cases or domains.

## 🛠️ TODO: Implementation Steps

1. Data preparation
    - [X] Prepare personal context
    - [ ] Export Notion Database as a zip file
      - [ ] Prepare Notion system structure, tags, projects 
    - [ ] Export Pocket articles
      - [ ] Prepare Pocket system tags
    - [ ] Prepare sample web pages from bookmarks for scraping
      - [ ] Determine content page vs information source url
    - [ ] Prepare Todoist tags, projects and structure

2. Data Source Integration
    - [X] Implement [Notion API](https://developers.notion.com/reference/get-database) client
    - [ ] Notion: Process only pages with last_edited_time > than last_edited_time in graph
    - [ ] Implement Notion exported zip parser
    - [ ] Develop Pocket exported file parser
    - [ ] Develop Pocket API integration
    - [ ] Create a web scraper for processing URLs
    - [ ] Create unified data models 
    - [ ] Design a unified interface for data source processors

3. Content Processing
    - [ ] Implement entity extraction using NLP techniques
    - [ ] Develop an insight generation module using LLMs
    - [ ] Create a content summarization feature
    - [ ] Add file caching of raw and processed content
    - [ ] Create content embeddings for semantic search

4. Knowledge Graph Management
    - [X] Set up Neo4j database integration
    - [X] Implement node and relationship creation logic
    - [ ] Develop query methods for retrieving related content
    - [ ] Create visualizations for the knowledge graph

5. AI Agents
    - [ ] Design a flexible AI agent architecture
    - [ ] Implement specific agents for entity extraction, insight generation, and summarization
    - [ ] Develop a system for managing different LLM models and configurations

6. Pipeline Orchestration
    - [ ] Create a modular pipeline for processing content from ingestion to storage
    - [ ] Implement error handling and logging throughout the pipeline
    - [ ] Develop a system for incremental updates and change detection

7. User Interface
    - [ ] Add Streamlit for interacting with the system
    - [ ] Implement natural language querying of the knowledge graph
    - [ ] Create a web-based dashboard for visualizing insights and connections (InfraNodus-like)

8. Testing and Quality Assurance
    - [ ] Develop unit tests for each module
    - [ ] Implement integration tests for the entire pipeline
    - [ ] Create a suite of sample data for testing and demonstration
    - [ ] Evaluate entity extraction using different models, different contexts, and different prompts
    - [ ] Evaluate relation and weights creation using different models, different contexts, and different prompts
    - [ ] Evaluate GraphRAG using different embeddings and prompts

9. Advanced Features
    - [ ] Implement token-cost [estimation](https://github.com/AgentOps-AI/tokencost) 
    - [ ] Implement langfuse for agents and flow evaluation


## 🤝 Contributing
Knowledge Nexus is currently a personal project, but ideas and suggestions are welcome! Feel free to open an issue for discussion or submit a pull request with proposed changes.

## 🔒 Privacy and Data Handling
Knowledge Nexus is designed with your privacy in mind. All data is stored locally on your machine. The only external service used is OpenAI's API for AI processing, which is subject to their privacy policy and data handling practices.

---

Empower your mind, uncover hidden insights, and navigate your personal sea of knowledge with unprecedented ease. Welcome to Knowledge Nexus – where your information comes to life!
