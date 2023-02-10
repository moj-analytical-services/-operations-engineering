from github import Github


class GithubService:
    def __init__(self, org_token: str) -> None:
        self.client = Github(org_token)
