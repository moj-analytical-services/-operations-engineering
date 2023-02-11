import logging

from github import Github


class GithubService:
    def __init__(self, org_token: str, organisation_name: str) -> None:
        self.client = Github(org_token)
        self.organisation_name = organisation_name

    def get_outside_collaborators_login_names(self) -> list[str]:
        logging.info("Getting Outside Collaborators Login Names")
        outside_collaborators = self.client.get_organization(self.organisation_name).get_outside_collaborators() or []
        return [outside_collaborator.get("login") for outside_collaborator in outside_collaborators]
