import logging
import re
from typing import List

import tiktoken
from langchain_openai import OpenAIEmbeddings

from graph_rag.data_model.graph_data_classes import GraphPage, ProcessedData, Chunk, PageType
from graph_rag.processor.base_processor import Processor
from graph_rag.utils import cache_util
from graph_rag.utils.logging import LoggingProgressBar, ProgressBarHandler

CACHE_FILE_NAME = 'chunked_pages.json'

logger = logging.getLogger(__name__)


class TextCleaner:
    @staticmethod
    def clean(text: str) -> str:
        # Remove special characters but keep basic punctuation
        cleaned = re.sub(r'[^a-zA-Z0-9\s.,!?]', '', text)
        # Remove extra whitespace
        return re.sub(r'\s+', ' ', cleaned).strip()


class TokenCounter:
    def __init__(self, model_name: str):
        self.encoder = tiktoken.encoding_for_model(model_name=model_name)

    def count(self, text: str) -> int:
        return len(self.encoder.encode(text))


class ChunkCreator:
    def __init__(self, chunk_size: int, chunk_overlap: int, token_counter: TokenCounter):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.token_counter = token_counter

    def create_chunks(self, page: GraphPage) -> List[str]:
        constant_part = self._create_constant_part(page)
        constant_token_count = self.token_counter.count(constant_part)
        available_tokens = self.chunk_size - constant_token_count

        chunks = []
        start = 0
        while page.content and start < len(page.content):
            chunk_end = self._find_chunk_end(page.content, start, available_tokens)
            chunk = page.content[start:chunk_end]
            full_chunk_text = constant_part + chunk
            chunks.append(full_chunk_text)

            if chunk_end == len(page.content):
                break

            start = max(chunk_end - self.chunk_overlap, start + 1)

        # If no chunks were created (i.e., the content was shorter than available_tokens),
        # create a single chunk with all the content
        if not chunks:
            embedded_part = f"{constant_part if constant_part else ''}{page.content if page.content else ''}"
            chunks.append(embedded_part)

        return chunks

    @staticmethod
    def _create_constant_part(page: GraphPage) -> str:
        return f"Title: {page.title}\nLast edited time: {page.last_edited_time}\n\nContent:\n"

    def _find_chunk_end(self, content: str, start: int, available_tokens: int) -> int:
        """Find the largest chunk that fits within the token limit."""
        end = len(content)
        while start <= end:
            mid = (start + end) // 2
            chunk = content[start:mid]
            if self.token_counter.count(chunk) <= available_tokens:
                if mid == end or self.token_counter.count(content[start:mid + 1]) > available_tokens:
                    return mid
                start = mid + 1
            else:
                end = mid - 1
        return start


class ContentChunkerAndEmbedder(Processor):
    def __init__(self):
        super().__init__()
        self.model = self.config.EMBEDDINGS_MODEL
        self.embeddings = OpenAIEmbeddings(
            model=self.model,
            openai_api_base=self.config.EMBEDDINGS_BASE_URL,
            openai_api_key=self.config.EMBEDDINGS_API_KEY
        )
        self.token_counter = TokenCounter(self.model)
        self.chunk_creator = ChunkCreator(
            self.config.EMBEDDINGS_MAX_TOKENS,
            self.config.EMBEDDINGS_OVERLAP,
            self.token_counter
        )
        self.text_cleaner = TextCleaner()

    def process(self, processed_content: ProcessedData):
        logger.info("Processing content chunks and embeddings")
        if self.config.CACHE_ENABLED:
            root_page_id = self.config.NOTION_ROOT_PAGE_ID
            try:
                processed_content.pages = cache_util.load_prepared_pages_from_cache(root_page_id, CACHE_FILE_NAME)
                logger.info("Chunked pages loaded from cache")
                return
            except:
                logger.warning("No cache found for chunked pages. Processing from scratch.")

        progress_bar = LoggingProgressBar(len(processed_content.pages), prefix='Processing:',
                                          suffix=f"Complete out of {len(processed_content.pages)} pages ", length=50)
        handler = ProgressBarHandler(progress_bar)
        logger.addHandler(handler)
        progress_bar.start()
        for _, page in processed_content.pages.items():
            progress_bar.update()
            if page.type in [PageType.PAGE, PageType.DATABASE]:
                self._process_page(page)

        progress_bar.finish()
        logger.removeHandler(handler)

        if self.config.CACHE_ENABLED:
            cache_util.save_prepared_pages_to_cache(root_page_id, processed_content.pages, CACHE_FILE_NAME)
            logger.info("Chunked pages saved to cache")

    def _process_page(self, page: GraphPage) -> None:
        logger.debug(f"Chunking and embedding content of page {page.title}-{page.id}")
        chunks = self.chunk_creator.create_chunks(page)
        cleaned_chunks = [self.text_cleaner.clean(chunk) for chunk in chunks]
        chunk_embeddings = self.embeddings.embed_documents(cleaned_chunks)

        page.chunks = [
            Chunk(content=chunk, embedding=embedding)
            for chunk, embedding in zip(chunks, chunk_embeddings)
        ]
