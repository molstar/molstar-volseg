from app.requests.entries_request.i_entries_request import IEntriesRequest


class EntriesRequest(IEntriesRequest):
    def __init__(self, limit: int, keyword: str):
        self._limit = limit
        self._keyword = keyword

    def limit(self) -> int:
        return self._limit

    def keyword(self) -> str:
        return self._keyword


