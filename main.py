from fastapi import FastAPI, Request, Response
import os
import io
import aiofiles
from headers import filter_headers, is_multiple_pdf
from env import dotenv, tika_url
from pdf import page_requests
from requests import single_request
import pprint

dotenv()

tika_server = tika_url()

app = FastAPI()


@app.put("/tika/text")
async def tika(request: Request):

    async with aiofiles.tempfile.TemporaryFile(mode="w+b") as file:

        async for chunk in request.stream():
            await file.write(chunk)

        await file.seek(0)

        if is_multiple_pdf(request.headers):
            response = await page_requests(filter_headers(request.headers), tika_server, io.FileIO(file.fileno(), closefd=False))
        else:
            response = await single_request(filter_headers(request.headers), file, tika_server)

        return Response(headers=filter_headers(response[1]), content=response[0])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app,
                host=os.environ.get("HOST", "0.0.0.0"),
                port=int(os.environ.get("PORT", "9010"))
                )
