import aiohttp
import logging

logger = logging.getLogger("uvicorn.error")

async def single_request(headers, file, url: str):

  logger.info("Process single request!")

  async with aiohttp.ClientSession() as session:
    async with session.put(url, data=file, headers=headers) as response:
      text =  await response.text()
      headers = response.headers

      return (text, headers)