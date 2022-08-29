import json
import os
from urllib.parse import urlencode

import requests


class GithubClient:

    def __init__(self):
        self.token = os.environ.get("GIA_GITHUB_TOKEN")
        self.repo = os.environ.get("GIA_GITHUB_REPO").strip("/")
        print(self.token, self.repo)

    @property
    def _headers(self) -> dict:
        return  dict(
            Accept="Accept: application/vnd.github+json",
            Authorization=f"Bearer {self.token}"
        )

    def _fmt_issue_body(self, **kwargs):
        body_md_lines = []
        [body_md_lines.extend([f"#### {k}", v]) for k, v in kwargs.items()]
        body_md = "\n".join(body_md_lines)
        return body_md

    def create_issue(self, title, **kwargs):
        data = dict(
            title=title,
            body=self._fmt_issue_body(**kwargs),
            labels=[
                "from/chatbot1",
            ]
        )
        url = f"https://api.github.com/repos/{self.repo}/issues"
        response = requests.post(url,
                                 data=json.dumps(data),
                                 headers=self._headers)
        print(response)

    def search_issue(self, query):
        query += f" repo:{self.repo}"
        q = urlencode({"q": query})
        url = f"https://api.github.com/search/issues?{q}"
        # print(url)
        response = requests.get(url, headers=self._headers)
        data = response.json()
        if data.get('total_count'):
            return [{item.get("title"): item.get("url")} for item in data.get("items", [])]
        else:
            return None


if __name__ == '__main__':
    gc = GithubClient()

    title = "Problems signing in"
    qs = {
        "Description": title,
        "Version": "v0.1.2"
    }
    gc.create_issue(title=title, **qs)
    print(gc.search_issue(title))
