# Knowledge Nexus: Your AI-Powered Personal Knowledge Discovery Engine

## 🛠 Getting Started

1. install neo4j
2. install python
3. make and configure .env in root directory
4. adjust options in config/config.yaml if necessary
5. `pip install -r requirements.txt`
6. `python main.py`

## 🌟 Project Overview

Knowledge Nexus is an advanced personal knowledge management system that transforms the way individuals organize,
process, and discover insights from their digital content. By leveraging the power of AI and graph databases, this
project addresses the challenge of information overload and disconnected data silos that many knowledge workers face in
today's digital landscape.

Unlike traditional note-taking or knowledge management tools that rely heavily on manual organization, Knowledge Nexus
automates the process of extracting key concepts, generating insights, and creating meaningful connections across your
personal knowledge base.

## 🎯 Key Challenges Addressed

1. **Information Overload**: Knowledge Nexus cuts through the noise by automatically extracting key entities and
   insights from various content sources, helping you focus on what's important.

2. **Manual Processing Overhead**: Traditional tools require significant manual effort to organize and connect
   information. Knowledge Nexus automates this process, saving you time and cognitive effort.

3. **Limited Contextual Understanding**: While tools like Obsidian or Roam Research rely on explicit links, Knowledge
   Nexus uses AI to understand semantic and topical relationships, creating a richer, more nuanced knowledge graph.

4. **Disconnected Data Silos**: By importing and processing data from various sources into a single, interconnected
   knowledge graph, Knowledge Nexus bridges the gaps between your different information repositories.

5. **Difficulty in Discovering New Connections**: The AI-powered system can uncover non-obvious relationships between
   different pieces of information, potentially leading to new insights or ideas that you might have missed.

## 🚀 Key Features

- **Multi-Source Data Integration**: Import content from Notion, Pocket, web pages, and more (extensible architecture
  for adding new sources).
- **AI-Powered Entity and Topic Extraction**: Automatically identify and extract key entities and topics from processed
  content.
- **Intelligent Insight Generation**: Leverage AI to generate concise insights from your personal knowledge base.
- **Semantic Knowledge Graph Construction**: Build a comprehensive, interconnected graph of entities, topics, and
  content using Neo4j, reflecting not just explicit links but semantic relationships.
- **Contextual Querying and Exploration**: Easily retrieve relevant content and explore connections within your
  knowledge graph.
- **Personalized Knowledge Assistant**: Tailored to your specific needs and preferences, helping you find tools,
  frameworks, and best practices aligned with your views.

## 👥 Who Is It For?

Knowledge Nexus is primarily designed for individual users who:

- Deal with large amounts of information from various sources
- Seek to uncover new insights and connections within their knowledge base
- Want to reduce the cognitive overhead of manual knowledge management
- Are looking for a personal research assistant to aid in complex tasks or decision-making

## 🔗 Supported Notion Links

| Type                                     | Parse Markdown Text | Parse References | Recursive Parsing |
|------------------------------------------|:-------------------:|:----------------:|:-----------------:|
| **Page Properties**                      |
| Title                                    |          ✅          |        ✅         |         ✅         |
| Rich Text                                |          ✅          |        ✅         |         ✅         |
| Select                                   |          ✅          |       N/A        |        N/A        |
| Status                                   |          ✅          |       N/A        |        N/A        |
| Multi-select                             |          ✅          |       N/A        |        N/A        |
| Number                                   |          ✅          |       N/A        |        N/A        |
| Date                                     |          ✅          |       N/A        |        N/A        |
| People                                   |          ✅          |       N/A        |        N/A        |
| Files                                    |          ✅          |        ❌         |        N/A        |
| Checkbox                                 |          ✅          |       N/A        |        N/A        |
| URL                                      |          ✅          |        ✅         |         ❌         |
| Email                                    |          ✅          |       N/A        |        N/A        |
| Phone Number                             |          ✅          |       N/A        |        N/A        |
| Formula                                  |          ✅          |       N/A        |        N/A        |
| Relation                                 |          ✅          |        ✅         |         ✅         |
| Rollup                                   |          ✅          |       N/A        |        N/A        |
| Created Time                             |          ✅          |       N/A        |        N/A        |
| Created By                               |          ✅          |       N/A        |        N/A        |
| Last Edited Time                         |          ✅          |       N/A        |        N/A        |
| Last Edited By                           |          ✅          |       N/A        |        N/A        |
| Unique ID                                |          ✅          |       N/A        |        N/A        |
| Verification                             |          ✅          |       N/A        |        N/A        |
| **Database Properties**                  |
| Title                                    |          ✅          |        ❌         |         ❌         |
| Rich Text                                |         N/A         |       N/A        |        N/A        |
| Select                                   |          ❌          |       N/A        |        N/A        |
| Multi-select                             |          ❌          |       N/A        |        N/A        |
| Date                                     |         N/A         |       N/A        |        N/A        |
| People                                   |         N/A         |       N/A        |        N/A        |
| Files                                    |         N/A         |       N/A        |        N/A        |
| Checkbox                                 |         N/A         |       N/A        |        N/A        |
| URL                                      |         N/A         |       N/A        |        N/A        |
| Email                                    |         N/A         |       N/A        |        N/A        |
| Phone Number                             |         N/A         |       N/A        |        N/A        |
| Formula                                  |         N/A         |       N/A        |        N/A        |
| Relation                                 |          ❌          |        ❌         |         ❌         |
| Rollup                                   |         N/A         |       N/A        |        N/A        |
| Created Time                             |          ❌          |       N/A        |        N/A        |
| Created By                               |          ❌          |       N/A        |        N/A        |
| Last Edited Time                         |          ❌          |       N/A        |        N/A        |
| Last Edited By                           |          ❌          |       N/A        |        N/A        |
| **Blocks**                               |
| Paragraph                                |          ✅          |        ✅         |         ✅         |
| Heading 1                                |          ✅          |        ✅         |         ✅         |
| Heading 2                                |          ✅          |        ✅         |         ✅         |
| Heading 3                                |          ✅          |        ✅         |         ✅         |
| Bulleted List Item                       |          ✅          |        ✅         |         ✅         |
| Numbered List Item                       |          ✅          |        ✅         |         ✅         |
| To-do                                    |          ✅          |        ✅         |         ✅         |
| Toggle                                   |          ✅          |        ✅         |         ✅         |
| Code                                     |          ✅          |        ✅         |        N/A        |
| Quote                                    |          ✅          |        ✅         |         ✅         |
| Callout                                  |          ✅          |        ✅         |         ✅         |
| Mention (except mentions of page blocks) |          ✅          |        ✅         |        N/A        |
| Equation                                 |          ✅          |       N/A        |        N/A        |
| Bookmark                                 |          ✅          |        ✅         |        N/A        |
| Image                                    |          ✅          |        ❌         |        N/A        |
| Video                                    |          ✅          |        ❌         |        N/A        |
| Audio                                    |          ✅          |        ❌         |        N/A        |
| File                                     |          ✅          |        ❌         |        N/A        |
| PDF                                      |          ✅          |        ❌         |        N/A        |
| Embed                                    |          ✅          |        ✅         |        N/A        |
| Link Preview                             |          ✅          |        ✅         |        N/A        |
| Divider                                  |          ✅          |       N/A        |        N/A        |
| Table of Contents                        |          ✅          |       N/A        |        N/A        |
| Breadcrumb                               |          ✅          |       N/A        |        N/A        |
| Column List                              |          ✅          |       N/A        |        N/A        |
| Column                                   |          ✅          |       N/A        |        N/A        |
| Synced Block                             |          ✅          |        ✅         |         ✅         |
| Template                                 |          ✅          |        ✅         |         ✅         |
| Link to Page                             |          ✅          |        ✅         |         ✅         |
| Table                                    |          ✅          |       N/A        |        N/A        |
| Table Row                                |          ✅          |       N/A        |        N/A        |
| Child Page                               |          ✅          |        ✅         |         ✅         |
| Child Database (except linked and views) |          ✅          |        ✅         |         ✅         |
| **Comments**                             |          ❌          |        ❌         |         ❌         |

## 🔮 Future Enhancements

- Enhanced personalization through adaptive learning of user preferences and interests
- Integration with additional productivity tools and data sources
- Advanced visualization options for exploring your knowledge graph

## 🛠️ TODO: Implementation Steps

1. Data preparation
    - [X] Prepare personal context
    - [ ] Export Notion Database as a zip file
        - [X] Prepare Notion system structure, tags, projects
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
    - [X] Add file caching of raw and processed content
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

Knowledge Nexus is currently a personal project, but ideas and suggestions are welcome! Feel free to open an issue for
discussion or submit a pull request with proposed changes.

## 🔒 Privacy and Data Handling

Knowledge Nexus is designed with your privacy in mind. All data is stored locally on your machine. The only external
service used is OpenAI's API for AI processing, which is subject to their privacy policy and data handling practices.

---

Empower your mind, uncover hidden insights, and navigate your personal sea of knowledge with unprecedented ease. Welcome
to Knowledge Nexus – where your information comes to life!
