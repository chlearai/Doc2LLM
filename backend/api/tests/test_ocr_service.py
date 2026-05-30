from io import BytesIO

from app.ocr_service import TokenTrackingOCRService


class _Usage:
    total_tokens = 321


class _Message:
    content = "Extracted OCR text"


class _Choice:
    message = _Message()


class _Response:
    choices = [_Choice()]
    usage = _Usage()


class _Completions:
    def __init__(self):
        self.kwargs = None

    def create(self, **kwargs):
        self.kwargs = kwargs
        return _Response()


class _Client:
    def __init__(self):
        self.chat = type("Chat", (), {"completions": _Completions()})()


class _Repository:
    def __init__(self):
        self.calls = []

    def log_feature_usage(self, user_id, feature, model, tokens):
        self.calls.append((user_id, feature, model, tokens))


def test_token_tracking_ocr_service_logs_openai_usage():
    client = _Client()
    repository = _Repository()
    service = TokenTrackingOCRService(
        client=client,
        repository=repository,
        user_id="user-1",
    )

    result = service.extract_text(BytesIO(b"fake-image"))

    assert result.text == "Extracted OCR text"
    assert repository.calls == [("user-1", "ocr", "gpt-4o-mini", 321)]
    kwargs = client.chat.completions.kwargs
    assert kwargs["model"] == "gpt-4o-mini"
    assert kwargs["temperature"] == 0
    assert kwargs["max_tokens"] == 4096
