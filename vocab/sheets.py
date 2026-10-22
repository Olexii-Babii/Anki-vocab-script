import json
import logging
from dataclasses import dataclass

from .config import require

log = logging.getLogger(__name__)

HEADERS = ["word", "translation", "example", "added_at", "exported_at", "source"]
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly",
]
BATCH_SIZE = 500


@dataclass
class Row:
    row_no: int
    word: str
    translation: str
    example: str = ""
    added_at: str = ""
    exported_at: str = ""
    source: str = ""


def credentials():
    from google.oauth2 import service_account

    raw = require("GOOGLE_SERVICE_ACCOUNT_JSON")
    try:
        info = json.loads(raw)
    except json.JSONDecodeError:
        raise SystemExit("GOOGLE_SERVICE_ACCOUNT_JSON must contain the JSON key (file contents)")
    return service_account.Credentials.from_service_account_info(info, scopes=SCOPES)


def _col(index: int) -> str:
    return chr(ord("A") + index)


class Sheet:
    def __init__(self, creds, sheet_id: str, tab: str):
        from googleapiclient.discovery import build

        self.api = build("sheets", "v4", credentials=creds, cache_discovery=False).spreadsheets()
        self.sheet_id = sheet_id
        self.tab = tab
        self._ensure()

    def _ensure(self) -> None:
        meta = self.api.get(spreadsheetId=self.sheet_id).execute()
        titles = [s["properties"]["title"] for s in meta.get("sheets", [])]
        if self.tab not in titles:
            log.info("Creating sheet tab %s", self.tab)
            self.api.batchUpdate(
                spreadsheetId=self.sheet_id,
                body={"requests": [{"addSheet": {"properties": {"title": self.tab}}}]},
            ).execute()
        first = self.api.values().get(spreadsheetId=self.sheet_id, range=f"'{self.tab}'!A1:F1").execute()
        if first.get("values", [[]])[0][: len(HEADERS)] != HEADERS:
            if first.get("values"):
                raise SystemExit(f"First row of tab '{self.tab}' does not look like headers {HEADERS}")
            self.api.values().update(
                spreadsheetId=self.sheet_id, range=f"'{self.tab}'!A1",
                valueInputOption="RAW", body={"values": [HEADERS]},
            ).execute()

    def read_rows(self) -> list[Row]:
        resp = self.api.values().get(spreadsheetId=self.sheet_id, range=f"'{self.tab}'!A2:F").execute()
        rows = []
        for i, values in enumerate(resp.get("values", []), start=2):
            values = (values + [""] * len(HEADERS))[: len(HEADERS)]
            if not values[0].strip() and not values[1].strip():
                continue
            rows.append(Row(i, *[v.strip() for v in values]))
        return rows

    def append_rows(self, rows: list[list[str]]) -> None:
        for start in range(0, len(rows), BATCH_SIZE):
            chunk = rows[start : start + BATCH_SIZE]
            self.api.values().append(
                spreadsheetId=self.sheet_id, range=f"'{self.tab}'!A1",
                valueInputOption="RAW", insertDataOption="INSERT_ROWS", body={"values": chunk},
            ).execute()
            log.info("Written %d rows", start + len(chunk))

    def set_column(self, column: str, row_numbers: list[int], value: str) -> None:
        """Set `value` in `column` for the given rows in a single batch."""
        if not row_numbers:
            return
        col = _col(HEADERS.index(column))
        data = [{"range": f"'{self.tab}'!{col}{n}", "values": [[value]]} for n in row_numbers]
        for start in range(0, len(data), BATCH_SIZE):
            self.api.values().batchUpdate(
                spreadsheetId=self.sheet_id,
                body={"valueInputOption": "RAW", "data": data[start : start + BATCH_SIZE]},
            ).execute()


def open_sheet(tab: str) -> Sheet:
    return Sheet(credentials(), require("GOOGLE_SHEET_ID"), tab)
