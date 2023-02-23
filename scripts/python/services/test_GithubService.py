import unittest
from datetime import datetime, timedelta
from unittest.mock import call, MagicMock, Mock, patch

from github.NamedUser import NamedUser

from .GithubService import GithubService

ORGANISATION_NAME = "moj-analytical-services"
USER_ACCESS_REMOVED_ISSUE_TITLE = "User access removed, access is now via a team"


@patch("gql.transport.aiohttp.AIOHTTPTransport.__new__", new=MagicMock)
@patch("gql.Client.__new__")
@patch("github.Github.__new__")
class TestGithubServiceInit(unittest.TestCase):

    def test_sets_up_class(self, mock_github_client_core_api, mock_github_client_gql_api):
        mock_github_client_core_api.return_value = "test_mock_github_client_core_api"
        mock_github_client_gql_api.return_value = "test_mock_github_client_gql_api"
        github_service = GithubService("", ORGANISATION_NAME)
        self.assertEqual("test_mock_github_client_core_api",
                         github_service.github_client_core_api)
        self.assertEqual("test_mock_github_client_gql_api",
                         github_service.github_client_gql_api)
        self.assertEqual(ORGANISATION_NAME,
                         github_service.organisation_name)


@patch("gql.transport.aiohttp.AIOHTTPTransport.__new__", new=MagicMock)
@patch("gql.Client.__new__", new=MagicMock)
@patch("github.Github.__new__")
class TestGithubServiceGetOutsideCollaborators(unittest.TestCase):

    def test_returns_login_names(self, mock_github_client_core_api):
        mock_github_client_core_api.return_value.get_organization().get_outside_collaborators.return_value = [
            Mock(NamedUser, login="tom-smith"),
            Mock(NamedUser, login="john.smith"),
        ]
        response = GithubService(
            "", ORGANISATION_NAME).get_outside_collaborators_login_names()
        self.assertEqual(["tom-smith", "john.smith"], response)

    def test_calls_downstream_services(self, mock_github_client_core_api):
        mock_github_client_core_api.return_value.get_organization(
        ).get_outside_collaborators.return_value = []
        github_service = GithubService("", ORGANISATION_NAME)
        github_service.get_outside_collaborators_login_names()
        github_service.github_client_core_api.get_organization.assert_has_calls(
            [call(), call(ORGANISATION_NAME), call().get_outside_collaborators()])

    def test_returns_empty_list_when_collaborators_returns_none(self, mock_github_client_core_api):
        mock_github_client_core_api.return_value.get_organization(
        ).get_outside_collaborators.return_value = None
        github_service = GithubService("", ORGANISATION_NAME)
        response = github_service.get_outside_collaborators_login_names()
        self.assertEqual([], response)

    def test_returns_exception_when_collaborators_returns_exception(self, mock_github_client_core_api):
        mock_github_client_core_api.return_value.get_organization(
        ).get_outside_collaborators.side_effect = ConnectionError
        github_service = GithubService("", ORGANISATION_NAME)
        self.assertRaises(
            ConnectionError, github_service.get_outside_collaborators_login_names)

    def test_returns_exception_when_organization_returns_exception(self, mock_github_client_core_api):
        mock_github_client_core_api.return_value.get_organization.side_effect = ConnectionError
        github_service = GithubService("", ORGANISATION_NAME)
        self.assertRaises(
            ConnectionError, github_service.get_outside_collaborators_login_names)


@patch("gql.transport.aiohttp.AIOHTTPTransport.__new__", new=MagicMock)
@patch("gql.Client.__new__", new=MagicMock)
@patch("github.Github.__new__")
class TestGithubServiceCloseExpiredIssues(unittest.TestCase):
    DATE_BOUNDARY = 45
    ISSUE_STATE_CRITERIA = "open"

    inside_boundary_criteria = None
    on_boundary_criteria = None
    outside_boundary_criteria = None

    def setUp(self):
        now = datetime.now()
        self.inside_boundary_criteria = now - \
            timedelta(days=self.DATE_BOUNDARY + 1)
        self.on_boundary_criteria = now - timedelta(days=self.DATE_BOUNDARY)
        self.outside_boundary_criteria = now - \
            timedelta(days=self.DATE_BOUNDARY - 1)

    def happy_path_base_issue_mock(self, created_at=None, title=None,
                                   state=None) -> MagicMock:
        return MagicMock(created_at=created_at or self.inside_boundary_criteria,
                         title=title or USER_ACCESS_REMOVED_ISSUE_TITLE,
                         state=state or self.ISSUE_STATE_CRITERIA)

    def test_calls_downstream_services(self, mock_github_client_core_api):
        mock_issue = self.happy_path_base_issue_mock()
        mock_github_client_core_api.return_value.get_repo().get_issues.return_value = [
            mock_issue]
        github_service = GithubService("", ORGANISATION_NAME)
        github_service.close_expired_issues("test")
        github_service.github_client_core_api.get_repo.assert_has_calls(
            [call(), call('moj-analytical-services/test'), call().get_issues()])
        github_service.github_client_core_api.get_repo().get_issues.assert_has_calls(
            [call()])

    def test_sets_issues_to_closed_when_criteria_met(self, mock_github_client_core_api):
        mock_issue = self.happy_path_base_issue_mock()
        mock_github_client_core_api.return_value.get_repo().get_issues.return_value = [
            mock_issue]
        GithubService("", ORGANISATION_NAME).close_expired_issues("test")
        self.assertEqual(mock_issue.edit.call_args_list,
                         [call(state='closed')])

    def test_sets_issues_to_closed_when_criteria_met_and_date_is_on_boundary(self, mock_github_client_core_api):
        mock_issue = self.happy_path_base_issue_mock(
            created_at=self.on_boundary_criteria)
        mock_github_client_core_api.return_value.get_repo().get_issues.return_value = [
            mock_issue]
        GithubService("", ORGANISATION_NAME).close_expired_issues("test")
        self.assertEqual(mock_issue.edit.call_args_list,
                         [call(state='closed')])

    def test_does_not_edit_issue_when_title_criteria_not_met(self, mock_github_client_core_api):
        mock_issue = self.happy_path_base_issue_mock(title="INCORRECT_TITLE")
        mock_github_client_core_api.return_value.get_repo().get_issues.return_value = [
            mock_issue]
        GithubService("", ORGANISATION_NAME).close_expired_issues("test")
        self.assertEqual(mock_issue.edit.call_args_list, [])

    def test_does_not_edit_issue_when_state_criteria_not_met(self, mock_github_client_core_api):
        mock_issue = self.happy_path_base_issue_mock(state="INCORRECT_STATE")
        mock_github_client_core_api.return_value.get_repo().get_issues.return_value = [
            mock_issue]
        GithubService("", ORGANISATION_NAME).close_expired_issues("test")
        self.assertEqual(mock_issue.edit.call_args_list, [])

    def test_does_not_edit_issue_when_empty_list(self, mock_github_client_core_api):
        mock_issue = self.happy_path_base_issue_mock()
        mock_github_client_core_api.return_value.get_repo().get_issues.return_value = []
        GithubService("", ORGANISATION_NAME).close_expired_issues("test")
        self.assertEqual(mock_issue.edit.call_args_list, [])

    def test_does_not_edit_issue_when_none_provided(self, mock_github_client_core_api):
        mock_issue = self.happy_path_base_issue_mock()
        mock_github_client_core_api.return_value.get_repo().get_issues.return_value = None
        GithubService("", ORGANISATION_NAME).close_expired_issues("test")
        self.assertEqual(mock_issue.edit.call_args_list, [])

    def test_throws_exception_when_client_throws_exception(self, mock_github_client_core_api):
        mock_github_client_core_api.return_value.get_repo = MagicMock(
            side_effect=ConnectionError)
        github_service = GithubService("", ORGANISATION_NAME)
        self.assertRaises(
            ConnectionError, github_service.close_expired_issues, "test")


@patch("gql.transport.aiohttp.AIOHTTPTransport.__new__", new=MagicMock)
@patch("gql.Client.__new__", new=MagicMock)
@patch("github.Github.__new__")
class TestGithubServiceCreateAnAccessRemovedIssueForUserInRepository(unittest.TestCase):
    def test_calls_downstream_services(self, mock_github_client_core_api):
        github_service = GithubService("", ORGANISATION_NAME)
        github_service.create_an_access_removed_issue_for_user_in_repository(
            "test_user", "test_repository")
        github_service.github_client_core_api.get_repo.assert_has_calls(
            [call('moj-analytical-services/test_repository'),
             call().create_issue(title=USER_ACCESS_REMOVED_ISSUE_TITLE, assignee='test_user',
                                 body='Hi there\n\nThe user test_user had Direct Member access to this repository and access via a team.\n\nAccess is now only via a team.\n\nYou may have less access it is dependant upon the teams access to the repo.\n\nIf you have any questions, please post in (#ask-operations-engineering)[https://mojdt.slack.com/archives/C01BUKJSZD4] on Slack.\n\nThis issue can be closed.')]

        )

    def test_throws_exception_when_client_throws_exception(self, mock_github_client_core_api):
        mock_github_client_core_api.return_value.get_repo = MagicMock(
            side_effect=ConnectionError)
        github_service = GithubService("", ORGANISATION_NAME)
        self.assertRaises(
            ConnectionError, github_service.create_an_access_removed_issue_for_user_in_repository, "test_user",
            "test_repository")


@patch("gql.transport.aiohttp.AIOHTTPTransport.__new__", new=MagicMock)
@patch("gql.Client.__new__", new=MagicMock)
@patch("github.Github.__new__")
class TestGithubServiceRemoveUserFromRepository(unittest.TestCase):
    def test_calls_downstream_services(self, mock_github_client_core_api):
        github_service = GithubService("", ORGANISATION_NAME)
        github_service.remove_user_from_repository(
            "test_user", "test_repository")
        github_service.github_client_core_api.get_repo.assert_has_calls([
            call('moj-analytical-services/test_repository'),
            call().remove_from_collaborators('test_user')
        ])

    def test_throws_exception_when_client_throws_exception(self, mock_github_client_core_api):
        mock_github_client_core_api.return_value.get_repo = MagicMock(
            side_effect=ConnectionError)
        github_service = GithubService("", ORGANISATION_NAME)
        self.assertRaises(
            ConnectionError, github_service.remove_user_from_repository, "test_user",
            "test_repository")


@patch("gql.transport.aiohttp.AIOHTTPTransport.__new__", new=MagicMock)
@patch("gql.Client.__new__", new=MagicMock)
@patch("github.Github.__new__")
class TestGithubServiceGetUserPermissionForRepository(unittest.TestCase):
    def test_calls_downstream_services(self, mock_github_client_core_api):
        mock_github_client_core_api.return_value.get_user.return_value = "mock_user"
        github_service = GithubService("", ORGANISATION_NAME)
        github_service.get_user_permission_for_repository(
            "test_user", "test_repository")
        github_service.github_client_core_api.get_user.assert_has_calls([
                                                                        call('test_user')])
        github_service.github_client_core_api.get_repo.assert_has_calls([
            call('moj-analytical-services/test_repository'),
            call().get_collaborator_permission('mock_user')
        ])

    def test_throws_exception_when_client_throws_exception(self, mock_github_client_core_api):
        mock_github_client_core_api.return_value.get_repo = MagicMock(
            side_effect=ConnectionError)
        github_service = GithubService("", ORGANISATION_NAME)
        self.assertRaises(
            ConnectionError, github_service.get_user_permission_for_repository, "test_user",
            "test_repository")


@patch("gql.transport.aiohttp.AIOHTTPTransport.__new__", new=MagicMock)
@patch("gql.Client.__new__", new=MagicMock)
@patch("github.Github.__new__")
class TestGithubServiceRemoveUserFromTeam(unittest.TestCase):
    def test_calls_downstream_services(self, mock_github_client_core_api):
        mock_github_client_core_api.return_value.get_user.return_value = "mock_user"
        github_service = GithubService("", ORGANISATION_NAME)
        github_service.remove_user_from_team("test_user", "test_repository")
        github_service.github_client_core_api.get_user.assert_has_calls([
                                                                        call('test_user')])
        github_service.github_client_core_api.get_organization.assert_has_calls([
            call('moj-analytical-services'),
            call().get_team('test_repository'),
            call().get_team().remove_membership('mock_user')
        ])

    def test_throws_exception_when_client_throws_exception(self, mock_github_client_core_api):
        mock_github_client_core_api.return_value.get_organization = MagicMock(
            side_effect=ConnectionError)
        github_service = GithubService("", ORGANISATION_NAME)
        self.assertRaises(
            ConnectionError, github_service.remove_user_from_team, "test_user", "test_repository")


@patch("gql.transport.aiohttp.AIOHTTPTransport.__new__", new=MagicMock)
@patch("gql.Client.__new__", new=MagicMock)
@patch("github.Github.__new__")
class TestGithubServiceAddUserToTeam(unittest.TestCase):
    def test_calls_downstream_services(self, mock_github_client_core_api):
        mock_github_client_core_api.return_value.get_user.return_value = "mock_user"
        github_service = GithubService("", ORGANISATION_NAME)
        github_service.add_user_to_team("test_user", 1)
        github_service.github_client_core_api.get_user.assert_has_calls([
            call('test_user')])
        github_service.github_client_core_api.get_organization.assert_has_calls([
            call('moj-analytical-services'),
            call().get_team(1),
            call().get_team().add_membership('mock_user')
        ])

    def test_throws_exception_when_client_throws_exception(self, mock_github_client_core_api):
        mock_github_client_core_api.return_value.get_organization = MagicMock(
            side_effect=ConnectionError)
        github_service = GithubService("", ORGANISATION_NAME)
        self.assertRaises(
            ConnectionError, github_service.remove_user_from_team, "test_user", 1)


if __name__ == "__main__":
    unittest.main()
