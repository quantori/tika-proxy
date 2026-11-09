import aiohttp
import logging

logger = logging.getLogger("uvicorn.error")

async def single_request(headers, file, url: str):
  """Forward the whole file to Tika unchanged. Returns (body, headers, status)."""

  logger.info("Process single request!")

  async with aiohttp.ClientSession() as session:
    async with session.put(url, data=file, headers=headers) as response:
      text =  await response.text()

      return (text, response.headers, response.status)
