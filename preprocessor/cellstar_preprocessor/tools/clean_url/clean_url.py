def clean_url(url: str):
    cleaned = url.split("?")[0]
    return cleaned