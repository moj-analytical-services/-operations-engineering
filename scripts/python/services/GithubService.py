import logging
from datetime import datetime, timedelta
from textwrap import dedent

from github import Github
from github.Issue import Issue
from gql import Client
from gql.transport.aiohttp import AIOHTTPTransport


class GithubService:
    USER_ACCESS_REMOVED_ISSUE_TITLE: str = "User access removed, access is now via a team"

    def __init__(self, org_token: str, organisation_name: str) -> None:
        self.github_client_core_api: Github = Github(org_token)
        self.github_client_gql_api: Client = Client(transport=AIOHTTPTransport(
            url="https://api.github.com/graphql",
            headers={"Authorization": f"Bearer {org_token}"},
        ), fetch_schema_from_transport=False)
        self.organisation_name: str = organisation_name

    def get_outside_collaborators_login_names(self) -> list[str]:
        logging.info("Getting Outside Collaborators Login Names")
        outside_collaborators = self.github_client_core_api.get_organization(
            self.organisation_name).get_outside_collaborators() or []
        return [outside_collaborator.login for outside_collaborator in outside_collaborators]

    def close_expired_issues(self, repository_name: str) -> None:
        logging.info(f"Closing expired issues for {repository_name}")
        issues = self.github_client_core_api.get_repo(
            f"{self.organisation_name}/{repository_name}").get_issues() or []
        for issue in issues:
            if self.__is_expired(issue):
                issue.edit(state="closed")
                logging.info(f"Closing issue in {repository_name}")

    def __is_expired(self, issue: Issue) -> bool:
        grace_period = issue.created_at + timedelta(days=45)
        return (issue.title == self.USER_ACCESS_REMOVED_ISSUE_TITLE
                and issue.state == "open"
                and grace_period < datetime.now())

    def create_an_access_removed_issue_for_user_in_repository(self, user_name: str, repository_name: str) -> None:
        logging.info(
            f"Creating an access removed issue for user {user_name} in repository {repository_name}")
        self.github_client_core_api.get_repo(f"{self.organisation_name}/{repository_name}").create_issue(
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

    def remove_user_from_repository(self, user_name: str, repository_name: str) -> None:
        logging.info(
            f"Removing user {user_name} from repository {repository_name}")
        self.github_client_core_api.get_repo(
            f"{self.organisation_name}/{repository_name}").remove_from_collaborators(user_name)

    def get_user_permission_for_repository(self, user_name: str, repository_name: str) -> str:
        logging.info(
            f"Getting permissions for user {user_name} from repository {repository_name}")
        user = self.github_client_core_api.get_user(user_name)
        return self.github_client_core_api.get_repo(
            f"{self.organisation_name}/{repository_name}").get_collaborator_permission(user)

    def remove_user_from_team(self, user_name: str, team_id: int) -> None:
        logging.info(f"Removing user {user_name} from team {team_id}")
        user = self.github_client_core_api.get_user(user_name)
        self.github_client_core_api.get_organization(self.organisation_name).get_team(team_id).remove_membership(
            user)

    def add_user_to_team(self, user_name: str, team_id: int) -> None:
        logging.info(f"Adding user {user_name} from team {team_id}")
        user = self.github_client_core_api.get_user(user_name)
        self.github_client_core_api.get_organization(
            self.organisation_name).get_team(team_id).add_membership(user)

    def create_new_team_with_repository(self, team_name: str, repository_name: str) -> None:
        logging.info(
            f"Creating team {team_name} for repository {repository_name}")
        repo = self.github_client_core_api.get_repo(
            f"{self.organisation_name}/{repository_name}")
        self.github_client_core_api.get_organization(self.organisation_name).create_team(
            team_name,
            [repo],
            "",
            "closed",
            "Automated generated team to grant users access to this repository",
        )

    def team_exists(self, team_name) -> bool:
        logging.info(f"Checking if team {team_name} exists")
        github_teams = self.github_client_core_api.get_organization(
            self.organisation_name).get_teams() or []
        return any(github_team.name == team_name for github_team in github_teams)

    def amend_team_permissions_for_repository(self, team_id: int, permission: str, repository_name: str) -> None:
        logging.info(
            f"Amending permissions for team {team_id} in repository {repository_name}")
        if permission == "read":
            permission = "pull"
        elif permission == "write":
            permission = "push"
        repo = self.github_client_core_api.get_repo(
            f"{self.organisation_name}/{repository_name}")
        self.github_client_core_api.get_organization("moj-analytical-services").get_team(
            team_id).update_team_repository(repo, permission)
