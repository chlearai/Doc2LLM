from app.models import ConversionRecord


class InMemoryMarkdownStorage:
    def __init__(self, bucket: str = "markdown-outputs") -> None:
        self.bucket = bucket
        self._objects: dict[str, str] = {}

    def path_for(self, record: ConversionRecord) -> str:
        return f"{self.bucket}/{record.user_id}/{record.id}/output.md"

    def upload_markdown(self, record: ConversionRecord, markdown: str) -> str:
        path = record.markdown_storage_path or self.path_for(record)
        self._objects[path] = markdown
        return path

    def get_markdown(self, path: str) -> str | None:
        return self._objects.get(path)

    def create_signed_url(self, path: str, expires_in: int = 300) -> str:
        if path not in self._objects:
            return ""
        return f"https://supabase.local/storage/v1/object/sign/{path}?expires_in={expires_in}"

    def delete(self, path: str | None) -> None:
        if path:
            self._objects.pop(path, None)
