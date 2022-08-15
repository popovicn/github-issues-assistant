import os

from github import Github


class GithubService:
    def __init__(self, token):
        self.token = token
        self.g = Github(self.token)

    def read_repos(self):
        for repo in self.g.get_user().get_repos():
            print(repo.name, repo.full_name)


if __name__ == '__main__':
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("No GITHUB_TOKEN")
        exit(1)

    g = GithubService(token)
    g.read_repos()
