import unittest
from unittest.mock import call, MagicMock, patch

from scripts.python.services.GithubService import GithubService

ORGANISATION_NAME = "moj-analytical-services"


class TestGithubService(unittest.TestCase):
    mock_github = None

    github_service = None

    def setUp(self):
        self.mock_github = MagicMock()
        self.patcher = patch(target="github.Github.__new__",
                             return_value=self.mock_github, autospec=True)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

        self.github_service = GithubService("", ORGANISATION_NAME)

    def tearDown(self):
        self.patcher.stop()

    def test_init_sets_up_class(self):
        self.assertIs(self.mock_github, self.github_service.client)
        self.assertEqual(ORGANISATION_NAME,
                         self.github_service.organisation_name)

    def test_get_outside_collaborators_login_names_returns_login_names(self):
        self.mock_github.get_organization().get_outside_collaborators.return_value = [{"login": "tom-smith"},
                                                                                      {"login": "john.smith"}]
        response = self.github_service.get_outside_collaborators_login_names()
        self.assertEqual(["tom-smith", "john.smith"], response)

    def test_get_outside_collaborators_login_names_calls_downstream_services(self):
        self.mock_github.get_organization().get_outside_collaborators.return_value = []
        self.github_service.get_outside_collaborators_login_names()
        self.mock_github.get_organization.assert_has_calls(
            [call(), call(ORGANISATION_NAME), call().get_outside_collaborators()])

    def test_get_outside_collaborators_login_names_returns_empty_list_when_collaborators_returns_none(self):
        self.mock_github.get_organization().get_outside_collaborators.return_value = None
        response = self.github_service.get_outside_collaborators_login_names()
        self.assertEqual([], response)

    def test_get_outside_collaborators_login_names_returns_exception_when_collaborators_returns_exception(self):
        self.mock_github.get_organization(
        ).get_outside_collaborators.side_effect = ConnectionError
        self.assertRaises(
            ConnectionError, self.github_service.get_outside_collaborators_login_names)

    def test_get_outside_collaborators_login_names_returns_exception_when_organization_returns_exception(self):
        self.mock_github.get_organization.side_effect = ConnectionError
        self.assertRaises(
            ConnectionError, self.github_service.get_outside_collaborators_login_names)


if __name__ == "__main__":
    unittest.main()
