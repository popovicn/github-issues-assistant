import json
import os
from datetime import datetime
from typing import List, Union
from urllib.parse import urlencode

import requests


class GithubIssueObj:

    def __init__(self, number, title, state, url, last_activity):
        self.number = number
        self.title = title
        self.state = state
        self.url = url
        self.last_activity = last_activity

    @classmethod
    def from_json(cls, data):
        return cls(
            number=data.get('number'),
            title=data.get('title'),
            state=data.get('state'),
            url=data.get('url'),
            last_activity=datetime.strptime(data.get('last_activity'), '%d.%m.%Y.')
        )

    def to_json(self):
        return dict(
            number=self.number,
            title=self.title,
            state=self.state,
            url=self.url,
            last_activity=self.last_activity.strftime('%d.%m.%Y.')
        )

    @classmethod
    def load(cls, data):
        return cls(
            number=data.get('number'),
            title=data.get('title'),
            state=data.get('state'),
            url=data.get('html_url'),
            last_activity=datetime.strptime(data.get('updated_at'), "%Y-%m-%dT%H:%M:%SZ")
        )

    @property
    def description(self):
        return f"Issue #{self.number} '{self.title}' is {self.state}. " \
               f"Last activity happened on {self.last_activity.strftime('%d.%m.%Y.')} " \
               f"You can track it at: {self.url}"

    @property
    def short_description(self):
        return f"{self.state.title()} issue #{self.number} '{self.title}' @ {self.url}"


class GithubClient:

    def __init__(self):
        self.token = os.environ.get("GIA_GITHUB_TOKEN")
        self.repo = os.environ.get("GIA_GITHUB_REPO").strip("/")
        self.mock = os.environ.get("GIA_ENV") != "production"
        self._static_label = "via:chatbot"

    @property
    def _headers(self) -> dict:
        return  dict(
            Accept="Accept: application/vnd.github+json",
            Authorization=f"Bearer {self.token}"
        )

    def _fmt_issue_body(self, user, data) -> str:
        body_md_lines = [
            f"> _This issue was submitted by user @{user} "
            f"via [popovicn/github-issues-assistant]"
            f"(https://github.com/popovicn/github-issues-assistant)_"
        ]
        possible_duplicates = data.pop("possible_duplicates", None)
        if possible_duplicates:
            duplicate_alert = "> ?????? _Possible duplicate of"
            for pd in possible_duplicates:
                duplicate_alert += f" #{GithubIssueObj.from_json(pd).number}"
            body_md_lines.append(duplicate_alert + "_")
        [body_md_lines.extend([f"### {k}", v]) for k, v in data.items()]
        body_md = "\n".join(body_md_lines)
        return body_md

    def create_issue(self, user, title, data) -> str:
        # if self.mock:
        #     return "<mock url>"
        labels = [self._static_label]
        custom_label = data.pop("label", None)
        if custom_label:
            labels.append(custom_label)
        data = dict(
            title=title,
            body=self._fmt_issue_body(user, data),
            labels=labels
        )
        url = f"https://api.github.com/repos/{self.repo}/issues"
        response = requests.post(url,
                                 data=json.dumps(data),
                                 headers=self._headers)
        if response.status_code == 201:
            return response.json().get("url")
        else:
            return None

    def get_issue(self, issue_number) -> Union[GithubIssueObj, None]:
        url = f"https://api.github.com/repos/{self.repo}/issues/{issue_number}"
        response = requests.get(url, headers=self._headers)
        if response.status_code == 200:
            return GithubIssueObj.load(response.json())
        else:
            return None

    def search_issue(self, query) -> List[GithubIssueObj]:
        query += f" repo:{self.repo}"
        q = urlencode({"q": query})
        url = f"https://api.github.com/search/issues?{q}"
        response = requests.get(url, headers=self._headers)
        if response.status_code != 200:
            return []
        data = response.json()
        if data.get('total_count'):
            return [GithubIssueObj.load(item) for item in data.get("items", [])]
        else:
            return []
