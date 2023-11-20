from urllib.parse import urlparse, urljoin

from bs4 import BeautifulSoup
from serpapi import GoogleSearch as _RunSearch
import requests


class SearchEngine:
    def __init__(self):
        self.last_search = {"res": [], "prompt": ""}
        with open("../keys/serp_api_key.txt") as file:
            self.key = file.read()

    def update_links(self, prompt, start_entry=0):
        params = {
            "q": prompt,
            "engine": "duckduckgo",
            "api_key": self.key,
            "start": start_entry
        }

        search = _RunSearch(params)
        raw_search_results = search.get_dict()

        results = []
        for curr_raw_result in raw_search_results["organic_results"]:
            results.append(curr_raw_result["link"])

        self.last_search["res"] = results
        self.last_search["prompt"] = prompt

    def get_first_website(self):
        return self.get_website(0)

    def get_website(self, link_number):
        website_url = self.last_search["res"][link_number]
        response = requests.get(website_url)
        # html = response.text

        website_content = response.content
        soup = BeautifulSoup(website_content, 'html.parser')
        link_tags = soup.find_all('link', rel='stylesheet')
        css_content = []
        for link in link_tags:
            css_url = link.get('href')
            if not bool(urlparse(css_url).netloc):
                css_url = urljoin(website_url, css_url)
            css_response = requests.get(css_url)
            if css_response.status_code == 200:
                css_content.append(css_response.text)

        return {'html': soup.prettify(), 'css': css_content}


# Use case:
if __name__ == '__main__':
    # Create the engine
    search_engine = SearchEngine()
    # Use update-links method to refresh the search results (stored inside the class).
    # Start entry is 0 by default, it's the pagination offset
    search_engine.update_links("Used Honda Sedan for sale with 130k or less miles under 6k in good condition within 30 miles of Atlanta", start_entry=0)
    # Open link (default opens 0th link, otherwise use link_number argument)
    page = search_engine.get_first_website()
    print('\n\n\n\u001b[32mHTML\u001b[0m\n', page['html'])
    print('\n\n\n\u001b[32mCSS\u001b[0m\n', page['css'])
    print()
