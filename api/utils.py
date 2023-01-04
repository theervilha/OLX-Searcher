import re

def find_url_in_text(text):
    match = re.search("(?P<url>https?://[^\s]+)", text)
    if match:
        return match.group("url")

def is_olx_url(link):
    return 'olx.com.br' in link
