import logging
import re

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
    def clean_markdown(text: str) -> str:
        # Convert headings to sentences
        text = re.sub(r'^#+\s*(.*?)$', r'\1.', text, flags=re.MULTILINE)

        # Remove special characters except those specified
        cleaned = re.sub(r'[^a-zA-Z0-9\s.,!?;:/+\-]', '', text)

        # Remove extra whitespace
        return re.sub(r'\s+', ' ', cleaned).strip()


class TokenCounter:
    def __init__(self, model_name: str):
        try:
            encoder = tiktoken.encoding_for_model(model_name=model_name)
        except KeyError:
            logger.warning(f"Model {model_name} not found in tiktoken. Using cl100k_base instead.")
            encoder = tiktoken.get_encoding("cl100k_base")
        self.encoder = encoder

    def count(self, text: str) -> int:
        return len(self.encoder.encode(text, disallowed_special=()))


class ChunkCreator:
    def __init__(self, chunk_size: int, chunk_overlap: int, token_counter: TokenCounter):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.token_counter = token_counter

    def create_chunks(self, page: GraphPage) -> list[str]:
        constant_part = self._create_constant_part_for_content(page)  # TODO limit so it wouldn't exceed max chunk size
        constant_token_count = self.token_counter.count(constant_part)
        available_tokens = self.chunk_size - constant_token_count

        content_chunks = self.create_sentence_aware_chunks(page.content, available_tokens)

        if content_chunks:
            return [f"{constant_part}{chunk}" for chunk in content_chunks]
        else:
            # If no chunks were created, create a single chunk with page metadata
            return [self._create_constant_part(page)]

    def create_text_chunks(self, content: str, available_tokens: int) -> list[str]:
        chunks = []
        start = 0
        while content and start < len(content):
            chunk_end = self._find_chunk_end(content, start, available_tokens)
            chunk = content[start:chunk_end]
            chunks.append(chunk)

            if chunk_end == len(content):
                break

            start = max(chunk_end - self.chunk_overlap, start + 1)
        return chunks

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

    def create_sentence_aware_chunks(self, content: str, available_tokens: int) -> list[str]:
        overlap = self.chunk_overlap
        if available_tokens <= overlap:
            logger.warning(f"Chunk overlap {overlap} is greater than max content chunk size {available_tokens}. "
                           f"Skipping overlap.")
            overlap = 0
        chunks = []
        tokens = self.token_counter.encoder.encode(content, disallowed_special=())

        while tokens:
            chunk = tokens[:available_tokens]
            chunk_text = self.token_counter.encoder.decode(chunk)
            last_punctuation = max(
                chunk_text.rfind("."),
                chunk_text.rfind("?"),
                chunk_text.rfind("!"),
                chunk_text.rfind("\n"),
            )
            if last_punctuation != -1:
                chunk_text = chunk_text[: last_punctuation + 1]

            if chunk_text and (not chunk_text.isspace()):
                chunks.append(chunk_text)

            chunk_size = self.token_counter.count(chunk_text)
            if chunk_size >= len(tokens):
                break

            skip_tokens = chunk_size - overlap
            tokens = tokens[skip_tokens:]

        return chunks

    @staticmethod
    def _create_constant_part_for_content(page: GraphPage) -> str:
        return f"{ChunkCreator._create_constant_part(page)}\nContent:\n"

    @staticmethod
    def _create_constant_part(page: GraphPage) -> str:
        return f"Title: {page.title}\nLast edited time: {page.last_edited_time}\n"


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
        cleaned_chunks = [self.text_cleaner.clean_markdown(chunk) for chunk in chunks]
        chunk_embeddings = self.embeddings.embed_documents(cleaned_chunks)

        page.chunks = [
            Chunk(content=chunk, embedding=embedding)
            for chunk, embedding in zip(chunks, chunk_embeddings)
        ]
