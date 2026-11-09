
SAVE_HEADERS = ["content-type", "accept"]
PDF_MAGIC = b"%PDF-"

def filter_headers(src: dict)-> dict:
  dst = dict()
  for hdr in src.keys():
    if hdr.lower() in SAVE_HEADERS:
      dst[hdr] = src[hdr]

  return dst

def content_type(src: dict)->str:
  """The media type of the request without parameters, lower-cased; "" if absent."""
  for hdr in src.keys():
    if hdr.lower() == "content-type":
      return src[hdr].split(";")[0].strip().lower()

  return ""

def is_pdf(head: bytes, src: dict)->bool:
  """A request carries a PDF when the body starts with the PDF magic bytes, or
  when the client says so. The content check comes first: Open WebUI (0.6.35+)
  sends no Content-Type at all, and browsers get the type wrong."""
  return head.startswith(PDF_MAGIC) or content_type(src) == "application/pdf"
