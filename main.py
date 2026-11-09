from fastapi import FastAPI, Request, Response
import os
import io
import logging
import aiofiles
import aiohttp
from headers import filter_headers, is_pdf, content_type, PDF_MAGIC
from env import dotenv, tika_url
from pdf import page_requests, PdfSplitError, PageParseError, ClientDisconnected
from requests import single_request

dotenv()

tika_server = tika_url()

logger = logging.getLogger("uvicorn.error")

app = FastAPI()


@app.get("/healthcheck")
async def healthcheck():
    return Response(status_code=200, content="ok", headers={ "Content-Type": "text/plain"})


@app.put("/tika/text")
async def tika(request: Request):

    async with aiofiles.tempfile.TemporaryFile(mode="w+b") as file:

        size = 0
        async for chunk in request.stream():
            size += len(chunk)
            await file.write(chunk)

        await file.seek(0)
        head = os.pread(file.fileno(), len(PDF_MAGIC), 0)  # leaves the file offset alone

        headers = filter_headers(request.headers)
        pdf = is_pdf(head, request.headers)

        logger.info(f"PUT /tika/text: {size} bytes, "
                    f"content-type={content_type(request.headers) or '-'}, pdf={pdf}")

        try:
            if pdf:
                try:
                    # PyPDF2 gets its own in-memory copy. Sharing the temp file's
                    # descriptor with a second file object desynchronises the
                    # buffered wrapper, and closing it later fails with EINVAL.
                    body, response_headers, status = await page_requests(
                        headers, tika_server, io.BytesIO(await file.read()), request.is_disconnected)
                except PdfSplitError as e:
                    logger.warning(f"Cannot split pdf ({e}); sending it to Tika as one request")
                    await file.seek(0)
                    body, response_headers, status = await single_request(headers, file, tika_server)
            else:
                body, response_headers, status = await single_request(headers, file, tika_server)
        except PageParseError as e:
            logger.error(f"Pdf page processing failed: {e}")
            return Response(status_code=502, content=f"tika-proxy: {e}", media_type="text/plain")
        except ClientDisconnected as e:
            # Nobody is listening any more (Envoy/ALB timeout, caller gone). Stop
            # burning Tika CPU on the rest of the document.
            logger.warning(f"Pdf processing stopped: {e}")
            return Response(status_code=499, content=f"tika-proxy: {e}", media_type="text/plain")
        except aiohttp.ClientError as e:
            logger.error(f"Tika unreachable: {type(e).__name__}: {e}")
            return Response(status_code=502, content=f"tika-proxy: Tika unreachable: {e}",
                            media_type="text/plain")

        return Response(status_code=status, headers=filter_headers(response_headers), content=body)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app,
                host=os.environ.get("HOST", "0.0.0.0"),
                port=int(os.environ.get("PORT", "9010"))
                )
