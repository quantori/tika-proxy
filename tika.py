import asyncio
import json


class TikaCollect():
    data: str
    headers: dict
    request: dict

    def __init__(self):
        self.data = ""
        self.headers = dict()
        self.request = dict()

    async def async_collect(self, tasks: list):

        responses = await asyncio.gather(*tasks)

        for req in range(len(responses)):
            try:
                tika: dict = json.loads(responses[req][0])
                self.data += tika["X-TIKA:content"]

                if len(self.headers.keys) == 0:
                    self.headers = tika
                    del self.headers["X-TIKA:content"]
                    self.request = responses[req][1]
            except:
                pass

    def get_request(self)->list:
      self.request["X-TIKA:content"] = self.data
      return (json.dumps(self.request), self.headers)
