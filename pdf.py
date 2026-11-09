from PyPDF2 import PdfReader, PdfWriter
from aiofiles import tempfile
import os
import time
import aiohttp
import asyncio
import logging
from tika import TikaCollect

CHUNK = int(os.environ.get("TIKA_CHUNK", "8"))
RETRY_DELAY = float(os.environ.get("TIKA_RETRY_DELAY", "3"))

logger = logging.getLogger("uvicorn.error")


class PdfSplitError(Exception):
    """The file cannot be split into pages (encrypted, malformed, empty)."""


class PageParseError(Exception):
    """Tika failed, twice, on every page tried so far: it is not working at all."""


class ClientDisconnected(Exception):
    """The client went away mid-document; the remaining pages were not parsed."""


def split_pages(file, temp_dir: str) -> list:
    """Write every page of the PDF as its own file into temp_dir. Returns the paths."""
    base = os.path.abspath(temp_dir)
    paths = []

    try:
        pdf = PdfReader(stream=file)

        if pdf.is_encrypted and not pdf.decrypt(""):
            raise PdfSplitError("encrypted PDF")

        for index, page in enumerate(pdf.pages):
            writer = PdfWriter()
            writer.add_page(page)

            path = os.path.abspath(os.path.join(base, f"page-{index:05d}.pdf"))
            if not path.startswith(base):
                raise PdfSplitError("unexpected page path")

            with open(path, "wb") as out:
                writer.write(out)

            paths.append(path)
    except PdfSplitError:
        raise
    except Exception as e:  # PyPDF2 raises many exception types on malformed input
        raise PdfSplitError(f"{type(e).__name__}: {e}") from e

    if not paths:
        raise PdfSplitError("no pages")

    return paths


async def single_page(headers, url, path: str, session):
    with open(path, "rb") as page:
        async with session.put(url, data=page, headers=headers) as response:
            return (await response.read(), response.headers, response.status)


async def page_requests(headers, url, file, is_disconnected=None):
    """Split a PDF into pages and parse them on Tika, CHUNK pages at a time.

    A page that fails (connection error, non-200, bad JSON) is retried once
    after RETRY_DELAY seconds, which covers a Tika worker restart. A page that
    fails again is skipped, with an error in the log: the text is assembled
    from the other pages. The request only fails when not a single page has
    been parsed by then, i.e. Tika is not working at all. Between batches,
    is_disconnected() (if given) is awaited; when the client has gone, e.g. a
    proxy in front timed out, the remaining pages are not sent to Tika.
    Returns (body, headers, status) shaped like a single Tika response. Raises
    PdfSplitError if the file cannot be split, PageParseError if Tika fails on
    every page, ClientDisconnected if the client left."""

    headers = {k: v for k, v in headers.items() if k.lower() != "content-type"}
    headers["Content-Type"] = "application/pdf"

    async with tempfile.TemporaryDirectory() as temp_dir:
        started = time.monotonic()

        pages = await asyncio.to_thread(split_pages, file, temp_dir)
        total = len(pages)

        logger.info(f"Start pdf process! pages={total} chunk={CHUNK}")

        data = TikaCollect()
        retried = 0
        skipped = 0

        async with aiohttp.ClientSession() as session:

            async def parse(indices) -> list:
                """Send these pages to Tika concurrently; return the indices that failed."""
                results = await asyncio.gather(
                    *(single_page(headers, url, pages[i], session) for i in indices),
                    return_exceptions=True)  # one failed page must not cancel the others
                return data.collect(indices, results)

            for start in range(0, total, CHUNK):
                if is_disconnected is not None and await is_disconnected():
                    raise ClientDisconnected(f"client disconnected after {start} of {total} pages, "
                                             f"{time.monotonic() - started:.0f}s")

                batch = list(range(start, min(start + CHUNK, total)))

                logger.info(f"Process pages {batch[0] + 1}-{batch[-1] + 1} of {total}")

                failed = await parse(batch)

                if not failed:
                    continue

                logger.warning(f"Retrying pages {[i + 1 for i in failed]}: {data.last_error}")
                retried += len(failed)
                await asyncio.sleep(RETRY_DELAY)

                given_up = await parse(failed)

                if given_up and not data.texts:
                    # Nothing parsed so far: Tika is down or rejects everything,
                    # there is nothing worth returning.
                    raise PageParseError(data.last_error)

                if given_up:
                    skipped += len(given_up)
                    logger.error(f"Skipping pages {[i + 1 for i in given_up]} "
                                 f"after retry: {data.last_error}")

        logger.info(f"Pdf process done: pages={total} retried={retried} skipped={skipped} "
                    f"in {time.monotonic() - started:.1f}s")

        return data.get_request()
