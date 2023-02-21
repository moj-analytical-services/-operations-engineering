import logging
from datetime import datetime, timedelta

from github import Github
from github.Issue import Issue


class GithubService:
    def __init__(self, org_token: str, organisation_name: str) -> None:
        self.client: Github = Github(org_token)
        self.organisation_name: str = organisation_name

    def get_outside_collaborators_login_names(self) -> list[str]:
        logging.info("Getting Outside Collaborators Login Names")
        outside_collaborators = self.client.get_organization(
            self.organisation_name).get_outside_collaborators() or []
        return [outside_collaborator.get("login") for outside_collaborator in outside_collaborators]

    def close_expired_issues(self, repository_name: str):
        logging.info(f"Closing expired issues for {repository_name}")
        issues = self.client.get_repo(f"{self.organisation_name}/{repository_name}").get_issues() or []
        for issue in issues:
            if self.__is_expired(issue):
                issue.edit(state="closed")
                logging.info(f"Closing issue in {repository_name}")

    def __is_expired(self, issue: Issue):
        grace_period = issue.created_at + timedelta(days=45)
        return (issue.title == "User access removed, access is now via a team"
                and issue.state == "open"
                and grace_period < datetime.now())
