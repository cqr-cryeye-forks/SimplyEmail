#!/usr/bin/python
# -*- coding: utf-8 -*-
import requests


class Canary:
    def __init__(self, api_key: str, host: str = None, debug: bool = False):
        self.api_key = api_key
        self.session = requests.Session()
        self.url = f"http://{host}/_api/?key={api_key}" if debug else f"https://canar.io/_api/?key={api_key}"
        self.data = None

    def retrieve(self, url: str, data: dict = None, post: bool = False):
        try:
            if post:
                response = self.session.post(url, data=data)
            else:
                response = self.session.get(url)

            response.raise_for_status()  # Raise an error for bad status codes
            self.data = response.json()  # Parse the response JSON
        except requests.RequestException as e:
            print(f"Error during request to {url}: {e}")
            self.data = None

    def build_url(self, data: dict) -> str:
        params = '&'.join(f"{k}={v}" for k, v in data.items())
        return f"{self.url}&{params}"

    def search(self, query: str, bang: str = None):
        if bang:
            query = f"!{bang} {query}"
        url = self.build_url({'action': 'search', 'query': query})
        self.retrieve(url)
        return self.data

    def view(self, item: str):
        url = self.build_url({'action': 'view', 'item': item})
        self.retrieve(url)
        return self.data

    def store(self, title: str, text: str, source: str, source_url: str):
        if not title:
            title = 'Untitled'
        data = {'title': title, 'text': text, 'source': source, 'source_url': source_url}
        url = self.build_url({'action': 'store'})
        self.retrieve(url, data=data, post=True)

# Example usage:
# canary_instance = Canary(api_key='your_api_key_here')
# search_result = canary_instance.search('example query')
# print(search_result)
