import unittest
from unittest.mock import patch, MagicMock

from graph_rag.data_model.graph_data_classes import PageType, GraphPage
from graph_rag.processor.content_chunker_and_embedder import ChunkCreator, TokenCounter, TextCleaner


class TestTextCleaner(unittest.TestCase):
    def test_clean_markdown(self):
        cleaner = TextCleaner()
        input_text = "# Heading\nThis is a **test**!"
        expected_output = "Heading. This is a test!"
        self.assertEqual(cleaner.clean_markdown(input_text), expected_output)


class TestTokenCounter(unittest.TestCase):
    @patch('tiktoken.encoding_for_model')
    def test_token_counter_initialization_valid_model(self, mock_encoding):
        mock_encoder = MagicMock()
        mock_encoding.return_value = mock_encoder
        counter = TokenCounter("gpt-3.5-turbo")
        self.assertEqual(counter.encoder, mock_encoder)

    @patch('tiktoken.get_encoding')
    @patch('tiktoken.encoding_for_model', side_effect=KeyError)
    def test_token_counter_initialization_invalid_model(self, mock_encoding, mock_get_encoding):
        mock_encoder = MagicMock()
        mock_get_encoding.return_value = mock_encoder
        counter = TokenCounter("unknown-model")
        self.assertEqual(counter.encoder, mock_encoder)
        mock_get_encoding.assert_called_once_with("cl100k_base")

    @patch('tiktoken.encoding_for_model')
    def test_count(self, mock_encoding):
        mock_encoder = MagicMock()
        mock_encoder.encode.return_value = ['token1', 'token2', 'token3']
        mock_encoding.return_value = mock_encoder
        counter = TokenCounter("gpt-3.5-turbo")
        result = counter.count("Some text")
        self.assertEqual(result, 3)


class TestChunkCreator(unittest.TestCase):
    def setUp(self):
        self.token_counter = MagicMock()
        self.token_counter.count.side_effect = lambda text: len(text.split())
        self.chunk_creator = ChunkCreator(chunk_size=12, chunk_overlap=2, token_counter=self.token_counter)

    def test_create_chunks(self):
        mock_encoder = MagicMock()
        mock_encoder.encode.side_effect = lambda text, disallowed_special=None: text.split()
        mock_encoder.decode.side_effect = lambda tokens: ' '.join(tokens)
        self.token_counter.encoder = mock_encoder

        page = GraphPage(id="1", title="Test Page", type=PageType.PAGE, content="This is a test content.",
                         last_edited_time="2024-01-01", url="")
        result = self.chunk_creator.create_chunks(page)
        expected_chunks = ['Title: Test Page\nLast edited time: 2024-01-01\n\nContent:\nThis is a test',
                           'Title: Test Page\nLast edited time: 2024-01-01\n\nContent:\na test content.']
        self.assertEqual(2, len(result))
        self.assertEqual(expected_chunks, result)

    def test_create_text_chunks_empty_content(self):
        content = ""
        result = self.chunk_creator.create_text_chunks(content, available_tokens=5)
        self.assertEqual(result, [])

    def test_create_text_chunks_single_token(self):
        content = "Token"
        result = self.chunk_creator.create_text_chunks(content, available_tokens=5)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], "Token")

    def test_create_text_chunks_exact_chunk_size(self):
        content = "This is exact size."
        result = self.chunk_creator.create_text_chunks(content, available_tokens=4)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], "This is exact size.")

    def test_create_text_chunks_large_content(self):
        content = "This is a test content for chunking. Here we explore bigger sentence that consists of multiple chunks."
        result = self.chunk_creator.create_text_chunks(content, available_tokens=5)
        self.assertEqual(len(result), 3)
        self.assertEqual("This is a test content f", result[0])
        self.assertEqual(" for chunking. Here we explore bigger s", result[1])
        self.assertEqual(" sentence that consists of multiple chunks.", result[2])

    def test_create_text_chunks(self):
        content = ("This is a test content for chunking. Here we explore bigger sentence that consists of multiple "
                   "chunks.")
        result = self.chunk_creator.create_text_chunks(content, available_tokens=5)
        self.assertEqual(3, len(result))
        self.assertEqual("This is a test content f", result[0])
        self.assertEqual(" for chunking. Here we explore bigger s", result[1])
        self.assertEqual(" sentence that consists of multiple chunks.", result[2])

    @patch('tiktoken.encoding_for_model')
    def test_create_sentence_aware_chunks(self, mock_encoding):
        mock_encoder = MagicMock()
        mock_encoder.encode.side_effect = lambda text, disallowed_special=None: text.split()
        mock_encoder.decode.side_effect = lambda tokens: ' '.join(tokens)
        self.token_counter.encoder = mock_encoder

        content = "This is a sentence. This is another one!"
        result = self.chunk_creator.create_sentence_aware_chunks(content, available_tokens=6)

        expected_chunks = ["This is a sentence.", "a sentence. This is another one!"]
        self.assertEqual(expected_chunks, result)

    def test_create_sentence_aware_chunks_no_punctuation(self):
        mock_encoder = MagicMock()
        mock_encoder.encode.side_effect = lambda text, disallowed_special=None: text.split()
        mock_encoder.decode.side_effect = lambda tokens: ' '.join(tokens)
        self.token_counter.encoder = mock_encoder
        content = ("This is an example of a very long sentence that does not contain any punctuation marks "
                   "and is intended for testing purposes")
        result = self.chunk_creator.create_sentence_aware_chunks(content, available_tokens=10)
        self.assertEqual(["This is an example of a very long sentence that",
                          "sentence that does not contain any punctuation marks and is",
                          "and is intended for testing purposes"], result)


if __name__ == '__main__':
    unittest.main()
