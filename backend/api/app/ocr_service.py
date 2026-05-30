import base64
from pathlib import Path
import sys
from typing import Any, BinaryIO

backend_dir = Path(__file__).resolve().parents[2]
packages_dir = backend_dir / "markitdown-main" / "markitdown-main" / "packages"
for package in ("markitdown", "markitdown-ocr"):
    src = packages_dir / package / "src"
    src_text = str(src)
    if src.exists() and src_text not in sys.path:
        sys.path.insert(0, src_text)

from markitdown import StreamInfo
from markitdown_ocr import LLMVisionOCRService, OCRResult


OCR_MODEL = "gpt-4o-mini"
OCR_PROMPT = (
    "Extract all text from this image. Maintain the original layout and order. "
    "Return the extracted text with a one-sentence description of the content and context. "
    "Return in simple Markdown."
)


class TokenTrackingOCRService(LLMVisionOCRService):
    def __init__(
        self,
        *,
        client: Any,
        repository: Any,
        user_id: str,
        model: str = OCR_MODEL,
        default_prompt: str = OCR_PROMPT,
    ) -> None:
        super().__init__(client=client, model=model, default_prompt=default_prompt)
        self.repository = repository
        self.user_id = user_id

    def extract_text(
        self,
        image_stream: BinaryIO,
        prompt: str | None = None,
        stream_info: StreamInfo | None = None,
        **kwargs: Any,
    ) -> OCRResult:
        if self.client is None:
            return OCRResult(
                text="",
                backend_used="llm_vision",
                error="LLM client not configured",
            )

        try:
            image_stream.seek(0)
            content_type = stream_info.mimetype if stream_info else None
            if not content_type:
                content_type = "image/png"

            base64_image = base64.b64encode(image_stream.read()).decode("utf-8")
            data_uri = f"data:{content_type};base64,{base64_image}"
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=0,
                max_tokens=4096,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt or self.default_prompt},
                            {"type": "image_url", "image_url": {"url": data_uri}},
                        ],
                    }
                ],
            )

            usage = getattr(response, "usage", None)
            tokens = int(getattr(usage, "total_tokens", 0) or 0)
            if tokens > 0:
                self.repository.log_feature_usage(
                    self.user_id,
                    "ocr",
                    self.model,
                    tokens,
                )

            text = response.choices[0].message.content
            return OCRResult(
                text=text.strip() if text else "",
                backend_used="llm_vision",
            )
        except Exception as exc:
            return OCRResult(text="", backend_used="llm_vision", error=str(exc))
        finally:
            image_stream.seek(0)
