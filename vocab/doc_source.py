from pathlib import Path


def read_local(path: str) -> str:
    p = Path(path)
    if p.suffix.lower() == ".docx":
        import docx

        return "\n".join(par.text for par in docx.Document(str(p)).paragraphs)
    return p.read_text(encoding="utf-8")


def read_google_doc(credentials, doc_id: str) -> str:
    from googleapiclient.discovery import build

    drive = build("drive", "v3", credentials=credentials, cache_discovery=False)
    data = drive.files().export(fileId=doc_id, mimeType="text/plain").execute()
    return data.decode("utf-8") if isinstance(data, bytes) else data
