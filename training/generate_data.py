import os
import random

from github import Github


def read_issues(repo_name: str, filter_labels: tuple, limit=0):
    g = Github(os.environ.get("CHATBOT_GITHUB_TOKEN"))
    repo = g.get_repo(repo_name)
    ct = 0
    for issue in repo.get_issues():
        if any(label.name in filter_labels for label in issue.labels):
            print(issue.title)
            ct += 1
            if ct >= limit:
                return


def generate_versions():
    prefix = [
        "version",
        "version is",
        "i think version",
        "product version",
        "my version is",
        "the"
    ]
    suffix = [
        "is version",
        "version"
    ]
    with open('versions.txt', 'r') as f:
        for line in f.readlines():
            if not line.strip():
                continue
            entity = f"[{line.strip()}](version)"
            if random.random() < 0.3:
                print(f"{random.choice(prefix)} {entity}")
            elif random.random() < 0.3:
                print(f"{entity} {random.choice(suffix)}")
            else:
                print(entity)


if __name__ == '__main__':

    # read_issues('kubernetes/kubernetes', 'kind/bug', limit=100)
    generate_versions()