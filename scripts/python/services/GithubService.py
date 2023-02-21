import logging
from datetime import datetime, timedelta
from textwrap import dedent

from github import Github
from github.Issue import Issue


class GithubService:
    USER_ACCESS_REMOVED_ISSUE_TITLE: str = "User access removed, access is now via a team"

    def __init__(self, org_token: str, organisation_name: str) -> None:
        self.client: Github = Github(org_token)
        self.organisation_name: str = organisation_name

    def get_outside_collaborators_login_names(self) -> list[str]:
        logging.info("Getting Outside Collaborators Login Names")
        outside_collaborators = self.client.get_organization(
            self.organisation_name).get_outside_collaborators() or []
        return [outside_collaborator.login for outside_collaborator in outside_collaborators]

    def close_expired_issues(self, repository_name: str):
        logging.info(f"Closing expired issues for {repository_name}")
        issues = self.client.get_repo(
            f"{self.organisation_name}/{repository_name}").get_issues() or []
        for issue in issues:
            if self.__is_expired(issue):
                issue.edit(state="closed")
                logging.info(f"Closing issue in {repository_name}")

    def __is_expired(self, issue: Issue):
        grace_period = issue.created_at + timedelta(days=45)
        return (issue.title == self.USER_ACCESS_REMOVED_ISSUE_TITLE
                and issue.state == "open"
                and grace_period < datetime.now())

    def create_an_access_removed_issue_for_user_in_repository(self, user_name: str, repository_name: str):
        logging.info(f"Creating an access removed issue for user {user_name} in repository {repository_name}")
        self.client.get_repo(f"{self.organisation_name}/{repository_name}").create_issue(
            title=self.USER_ACCESS_REMOVED_ISSUE_TITLE,
            assignee=user_name,
            body=dedent(f"""
        Hi there
            
        The user {user_name} had Direct Member access to this repository and access via a team.
             
        Access is now only via a team.
             
        You may have less access it is dependant upon the teams access to the repo.
                   
        If you have any questions, please post in (#ask-operations-engineering)[https://mojdt.slack.com/archives/C01BUKJSZD4] on Slack.
            
        This issue can be closed.
        """).strip("\n")
        )
