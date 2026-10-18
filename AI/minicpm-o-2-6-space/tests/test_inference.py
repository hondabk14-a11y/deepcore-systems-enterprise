"""Offline tests; they do not validate a GPU or Hugging Face runtime."""
import unittest
from PIL import Image
from inference import DemoError, VisionRunner, clean_prompt, preprocess_image

class ModelStub:
    def __init__(self):
        self.calls = []
    def chat(self, **kwargs):
        self.calls.append(kwargs)
        return "The image contains a bridge."

class TestDemo(unittest.TestCase):
    def test_clean_prompt(self):
        self.assertEqual(clean_prompt("  Count objects  "), "Count objects")

    def test_blank_prompt_fails_before_loading(self):
        model = ModelStub()
        runner = VisionRunner(loader=lambda: (model, "test-tokenizer"))
        with self.assertRaisesRegex(DemoError, "Enter a question"):
            runner.answer(" ", [Image.new("RGB", (64, 64))])
        self.assertFalse(runner.loaded)

    def test_missing_image_fails_before_loading(self):
        model = ModelStub()
        runner = VisionRunner(loader=lambda: (model, "test-tokenizer"))
        with self.assertRaisesRegex(DemoError, "upload an image"):
            runner.answer("hello", [None])
        self.assertFalse(runner.loaded)

    def test_downscale(self):
        self.assertEqual(preprocess_image(Image.new("RGB", (2000, 1000))).size,
                         (1344, 672))

    def test_one_image_uses_upstream_call_shape(self):
        model = ModelStub()
        runner = VisionRunner(loader=lambda: (model, "test-tokenizer"))
        answer = runner.answer("What is this?", [Image.new("RGB", (16, 16))])
        self.assertEqual(answer, "The image contains a bridge.")
        self.assertEqual(len(model.calls), 1)
        self.assertEqual(len(model.calls[0]["msgs"][0]["content"]), 2)
        self.assertEqual(model.calls[0]["msgs"][0]["content"][1], "What is this?")
        self.assertEqual(model.calls[0]["tokenizer"], "test-tokenizer")
        self.assertTrue(runner.loaded)

    def test_two_image_compare_call_shape(self):
        model = ModelStub()
        runner = VisionRunner(loader=lambda: (model, "test-tokenizer"))
        runner.answer("What changed?", [Image.new("RGB", (16, 16)), Image.new("RGB", (16, 16))])
        self.assertEqual(len(model.calls[0]["msgs"][0]["content"]), 3)

    def test_reject_too_many_images(self):
        with self.assertRaisesRegex(DemoError, "one image"):
            VisionRunner(loader=lambda: (None, None)).answer("Compare", [1,2,3])

    def test_reject_large_dimensions(self):
        class Huge:
            size=(50000,50000)
            def convert(self,_):
                raise AssertionError("oversized image should not be loaded")
        with self.assertRaisesRegex(DemoError, "too large"):
            preprocess_image(Huge())

if __name__ == "__main__":
    unittest.main()
