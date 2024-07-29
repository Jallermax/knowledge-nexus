import unittest

from graph_rag.processor.content_chnker_and_embedder import ChunkCreator


class MockTokenCounter:
    def __init__(self, token_counts=None):
        self.token_counts = token_counts or {}

    def count(self, text):
        if self.token_counts:
            return sum(self.token_counts.get(word, 1) for word in text.split())
        else:
            return len(text.split())  # Simple word-based counting for Unicode tests


class TestFindChunkEnd(unittest.TestCase):
    def setUp(self):
        self.default_token_counter = MockTokenCounter({"word": 1, "longer": 2, "longest": 3})
        self.default_chunk_creator = ChunkCreator(chunk_size=10, chunk_overlap=2,
                                                  token_counter=self.default_token_counter)

    def test_find_chunk_end_exact_fit(self):
        content = "word word word word word word word word word word"
        end = self.default_chunk_creator._find_chunk_end(content, 0, 10)
        self.assertEqual(end, len(content))

    def test_find_chunk_end_partial_fit(self):
        content = "word word word word word word word word word word longer"
        end = self.default_chunk_creator._find_chunk_end(content, 0, 10)
        self.assertEqual(end, content.rindex("word") + 4)  # +4 to include the last "word"

    def test_find_chunk_end_single_long_word(self):
        content = "longest"
        end = self.default_chunk_creator._find_chunk_end(content, 0, 2)
        self.assertEqual(end, len(content))

    def test_find_chunk_end_mixed_lengths(self):
        content = "word longer longest word longer word"
        end = self.default_chunk_creator._find_chunk_end(content, 0, 8)
        self.assertEqual(end, content.index("longest"))

    def test_find_chunk_end_start_mid_content(self):
        content = "word word word word longer longest word word"
        start = content.index("longer")
        end = self.default_chunk_creator._find_chunk_end(content, start, 5)
        self.assertEqual(end, content.index("word", start + 6))

    def test_find_chunk_end_available_tokens_zero(self):
        content = "word word word"
        end = self.default_chunk_creator._find_chunk_end(content, 0, 0)
        self.assertEqual(end, 0)

    def test_find_chunk_end_empty_content(self):
        content = ""
        end = self.default_chunk_creator._find_chunk_end(content, 0, 10)
        self.assertEqual(end, 0)

    def test_find_chunk_end_unicode(self):
        unicode_token_counter = MockTokenCounter()
        unicode_chunk_creator = ChunkCreator(chunk_size=5, chunk_overlap=1, token_counter=unicode_token_counter)
        content = "Hello 你好 नमस्ते こんにちは"  # Mix of English, Chinese, Hindi, and Japanese
        end = unicode_chunk_creator._find_chunk_end(content, 0, 5)
        self.assertEqual(end, content.index("नमस्ते"))

    def test_find_chunk_end_with_punctuation(self):
        content = "Hello, world! How are you? I'm fine."
        end = self.default_chunk_creator._find_chunk_end(content, 0, 5)
        self.assertEqual(end, content.index("How"))

    def test_find_chunk_end_with_numbers(self):
        number_token_counter = MockTokenCounter({"1": 1, "10": 1, "100": 1, "word": 1})
        number_chunk_creator = ChunkCreator(chunk_size=5, chunk_overlap=1, token_counter=number_token_counter)
        content = "1 10 100 word word"
        end = number_chunk_creator._find_chunk_end(content, 0, 4)
        self.assertEqual(end, content.rindex("100") + 3)

    def test_find_chunk_end_with_newlines(self):
        content = "line1\nline2\nline3\nline4\nline5"
        end = self.default_chunk_creator._find_chunk_end(content, 0, 3)
        self.assertEqual(end, content.index("line4"))

    def test_find_chunk_end_exact_token_count(self):
        content = "word word word word word"
        end = self.default_chunk_creator._find_chunk_end(content, 0, 5)
        self.assertEqual(end, len(content))

    def test_find_chunk_end_large_content(self):
        content = "word " * 1000
        end = self.default_chunk_creator._find_chunk_end(content, 0, 100)
        self.assertEqual(end, 500)  # 100 words, each followed by a space (except the last one)


if __name__ == '__main__':
    unittest.main()
