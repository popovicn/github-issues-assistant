import os

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


if __name__ == '__main__':

    read_issues('kubernetes/kubernetes', 'kind/bug', limit=100)
    