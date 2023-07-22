from serpapi import GoogleSearch as _RunSearch
import json
import requests


class Search_Engine:
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

    def get_first_result_html(self):
        return requests.get(self.last_search["res"][0]).text

    def get_result_html(self, link_number):
        return requests.get(self.last_search["res"][link_number]).text


# Use case:
if __name__ == '__main__':
    # Create the engine
    search_engine = Search_Engine()
    # Use update-links method to refresh the search results (stored inside the class).
    # Start entry is 0 by default, it's the pagination offset
    search_engine.update_links("Chupa-chups", start_entry=0)
    # Open link (default opens 0th link, otherwise use link_number argument)
    print(search_engine.get_result_html(5))
