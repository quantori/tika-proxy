
SAVE_HEADERS = ["content-type", "accept"]

def filter_headers(src: dict)-> dict:
  dst = dict()
  for hdr in src.keys():
    if hdr.lower() in SAVE_HEADERS:
      dst[hdr] = src[hdr]

  return dst

def is_multiple_pdf(src: dict)->bool:

  type = "text/plain"
  length = 0

  for hdr in src.keys():

    match hdr.lower():
      case "content-type":
        type = src[hdr].lower()
      case "content-length":
        length = int(src[hdr].lower())

  return type == "application/pdf"
#and length > 2_000_000