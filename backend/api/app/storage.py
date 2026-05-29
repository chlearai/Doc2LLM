import httpx
from app.models import ConversionRecord


class SupabaseMarkdownStorage:
    def __init__(self, supabase_url: str, service_role_key: str, bucket: str = "markdown-outputs") -> None:
        self.supabase_url = supabase_url.rstrip("/")
        self.service_role_key = service_role_key
        self.bucket = bucket
        self.headers = {
            "Authorization": f"Bearer {service_role_key}",
        }
        self.client = httpx.Client(headers=self.headers, timeout=15.0)

    def path_for(self, record: ConversionRecord) -> str:
        return f"{record.user_id}/{record.id}/output.md"

    def upload_markdown(self, record: ConversionRecord, markdown: str) -> str:
        path = record.markdown_storage_path or self.path_for(record)
        url = f"{self.supabase_url}/storage/v1/object/{self.bucket}/{path}"
        headers = {
            **self.headers,
            "Content-Type": "text/markdown",
            "x-upsert": "true"
        }
        res = self.client.post(url, headers=headers, content=markdown.encode("utf-8"))
        res.raise_for_status()
        return path

    def get_markdown(self, path: str) -> str | None:
        url = f"{self.supabase_url}/storage/v1/object/{self.bucket}/{path}"
        res = self.client.get(url)
        if res.status_code == 404:
            return None
        res.raise_for_status()
        return res.text

    def create_signed_url(self, path: str, expires_in: int = 300) -> str:
        url = f"{self.supabase_url}/storage/v1/object/sign/{self.bucket}/{path}"
        headers = {
            **self.headers,
            "Content-Type": "application/json"
        }
        payload = {"expiresIn": expires_in}
        res = self.client.post(url, headers=headers, json=payload)
        res.raise_for_status()
        data = res.json()
        
        signed_path = data.get("signedURL") or data.get("signedUrl")
        if not signed_path:
            return ""
            
        if signed_path.startswith("http"):
            return signed_path
        return f"{self.supabase_url}{signed_path}"

    def delete(self, path: str | None) -> None:
        if not path:
            return
        url = f"{self.supabase_url}/storage/v1/object/{self.bucket}/{path}"
        res = self.client.delete(url)
        if res.status_code != 404:
            res.raise_for_status()


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

