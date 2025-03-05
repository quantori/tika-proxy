from dotenv import load_dotenv
import os

TIKA_PATH = "tika/text"

def dotenv():
  dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
  if os.path.exists(dotenv_path):
      load_dotenv(dotenv_path)


def tika_url():
  url = os.environ.get("TIKA_URL","http://localhost:9099")

  if not url.endswith("/"):
    url = url + "/"

  url = url + TIKA_PATH

  return url