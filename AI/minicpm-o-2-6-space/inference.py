"""MiniCPM-o 2.6 vision inference. Model credentials and weights are not bundled."""
from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Any, Callable, Sequence

MODEL_ID = "openbmb/MiniCPM-o-2_6"
MODEL_REVISION = "1bbb7660afda1ddf2db4eab70fce4bdbcbe1e22c"
MAX_INPUT_PIXELS = 20_000_000
MAX_SIDE = 1344
MAX_PROMPT_CHARS = 4000


class DemoError(Exception):
    """A failure with a safe message suitable for the Space UI."""


def preprocess_image(image: Any) -> Any:
    if image is None:
        raise DemoError("Please upload an image first.")
    if not hasattr(image, "size") or not hasattr(image, "convert"):
        raise DemoError("Please provide a valid image.")
    width, height = image.size
    if min(width, height) < 1 or width * height > MAX_INPUT_PIXELS:
        raise DemoError("Image is too large or invalid. Maximum: 20 million pixels.")
    copy = image.convert("RGB")
    copy.thumbnail((MAX_SIDE, MAX_SIDE))
    return copy


def clean_prompt(prompt: str) -> str:
    if not isinstance(prompt, str) or not prompt.strip():
        raise DemoError("Enter a question about your image.")
    if len(prompt) > MAX_PROMPT_CHARS:
        raise DemoError("Question is too long. Limit: 4,000 characters.")
    return prompt.strip()


def load_model() -> tuple[Any, Any]:
    import torch
    if not torch.cuda.is_available():
        raise DemoError("This model needs a CUDA GPU. Select L4 or larger in Space Settings.")
    from transformers import AutoModel, AutoTokenizer
    dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    model = AutoModel.from_pretrained(
        MODEL_ID,
        revision=MODEL_REVISION,
        trust_remote_code=True,
        torch_dtype=dtype,
        attn_implementation="sdpa",
        init_vision=True,
        init_audio=False,
        init_tts=False,
    ).eval().cuda()
    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_ID, revision=MODEL_REVISION, trust_remote_code=True
    )
    return model, tokenizer


@dataclass
class VisionRunner:
    loader: Callable[[], tuple[Any, Any]] = load_model

    def __post_init__(self) -> None:
        self._lock = threading.Lock()
        self._model: Any | None = None
        self._tokenizer: Any | None = None

    @property
    def loaded(self) -> bool:
        return self._model is not None

    def answer(self, prompt: str, images: Sequence[Any]) -> str:
        question = clean_prompt(prompt)
        if not images or len(images) > 2:
            raise DemoError("Provide one image, or two images for comparison.")
        processed = [preprocess_image(image) for image in images]
        with self._lock:
            if self._model is None:
                self._model, self._tokenizer = self.loader()
            import torch
            with torch.inference_mode():
                response = self._model.chat(
                    msgs=[{"role": "user", "content": [*processed, question]}],
                    tokenizer=self._tokenizer,
                    max_new_tokens=384,
                )
            return response if isinstance(response, str) else str(response)


runner = VisionRunner()


def analyze(image: Any, question: str) -> str:
    try:
        return runner.answer(question, [image])
    except DemoError as exc:
        return f"⚠️ {exc}"
    except Exception:
        return "⚠️ Inference failed. Check private Space logs."


def compare(first: Any, second: Any, question: str) -> str:
    try:
        return runner.answer(question, [first, second])
    except DemoError as exc:
        return f"⚠️ {exc}"
    except Exception:
        return "⚠️ Inference failed. Check private Space logs."


def extract_text(image: Any, instruction: str) -> str:
    return analyze(image, instruction or "Transcribe all clearly visible text and preserve line breaks.")
