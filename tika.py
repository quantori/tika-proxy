import json


class TikaCollect:
    """Collects per-page Tika responses and rebuilds one Tika-shaped response.

    Pages are stored by index, so a page that only succeeds on retry still lands
    in the right place. The metadata and HTTP headers of the first successful
    page stand in for the document's. Error messages number pages from 1, like
    a reader does."""

    def __init__(self):
        self.texts = dict()
        self.metadata = dict()
        self.headers = dict()
        self.last_error = None

    def collect(self, indices, results) -> list:
        """Store the good responses; return the indices of the failed pages."""
        failed = []

        for index, result in zip(indices, results):
            if isinstance(result, BaseException):
                self.last_error = f"page {index + 1}: {type(result).__name__}: {result}"
                failed.append(index)
                continue

            body, headers, status = result

            if status != 200:
                self.last_error = f"page {index + 1}: HTTP {status} {body[:200]!r}"
                failed.append(index)
                continue

            try:
                tika = json.loads(body)
            except ValueError as e:
                self.last_error = f"page {index + 1}: invalid JSON from Tika: {e}"
                failed.append(index)
                continue

            self.texts[index] = tika.get("X-TIKA:content") or ""

            if not self.metadata:
                self.metadata = {k: v for k, v in tika.items() if k != "X-TIKA:content"}
                self.headers = dict(headers)

        return failed

    def get_request(self):
        body = dict(self.metadata)
        body["X-TIKA:content"] = "".join(self.texts[i] for i in sorted(self.texts))

        return (json.dumps(body), self.headers, 200)
