from PyPDF2 import PdfReader, PdfWriter
from aiofiles import tempfile
import os
import aiohttp
import asyncio
import logging
import json
from tika import TikaCollect

CHUNK = int(os.environ.get("TIKA_CHUNK", "8"))

logger = logging.getLogger("uvicorn.error")


async def single_page(headers, url, file_name: str, session):

    with open(file_name, "rb") as file:
        async with session.put(url, data=file, headers=headers) as response:
            headers = response.headers
            text = await response.read()
            return (text, headers)


async def page_requests(headers, url, file):

    pdf = PdfReader(stream=file)

    pdf_pages = []

    async with tempfile.TemporaryDirectory() as temp_dir:

        logger.info("Start pdf process!")

        for page in range(len(pdf.pages)):
            pdf_writer = PdfWriter()
            pdf_writer.add_page(pdf.pages[page])

            out_file_name = os.path.join(temp_dir, f"page-{page:05d}.pdf")

            with open(out_file_name, 'wb') as out:
                pdf_writer.write(out)

            pdf_pages.append(out_file_name)

        pages = len(pdf_pages)

        data = TikaCollect()

        async with aiohttp.ClientSession() as session:

            tasks = []
            for page in range(pages):

                logger.info(f"Process page: {page} of {pages}")

                tasks.append(single_page(
                    headers, url, pdf_pages[page], session))

                if len(tasks) < CHUNK:
                    continue
                else:
                    await data.async_collect(tasks)
                    tasks.clear()

            if len(tasks) > 0:
                await data.async_collect(tasks)
                tasks.clear()

            return data.get_request()