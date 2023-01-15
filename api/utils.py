import re

def find_url_in_text(text):
    match = re.search("(?P<url>https?://[^\s]+)", text)
    if match:
        return match.group("url")

def is_olx_url(link):
    return 'olx.com.br' in link

def format_url_to_get_most_recent_products(link):
    # Put sf=1 as parameter in url to get most recent products
    if "sf=1" not in link:
        return link+'&sf=1'
    return link