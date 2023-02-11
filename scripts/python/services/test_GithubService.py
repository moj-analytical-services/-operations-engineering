import unittest
from unittest.mock import call, MagicMock, patch

from scripts.python.services.GithubService import GithubService


class TestGithubService(unittest.TestCase):
    def setUp(self):
        print("setting up")

    def tearDown(self):
        print("tearing down")

    def test_innit_sets_up_class(self):
        mock_github = MagicMock()
        patcher = patch(target="github.Github.__new__", return_value=mock_github, autospec=True)
        patcher.start()
        self.addCleanup(patcher.stop)

        github_service = GithubService("", "moj-analytical-services")

        self.assertIs(mock_github, github_service.client)
        self.assertEqual("moj-analytical-services", github_service.organisation_name)

        patcher.stop()

    def test_get_outside_collaborators_login_names_returns_login_names(self):
        mock_github = MagicMock()
        patcher = patch(target="github.Github.__new__", return_value=mock_github, autospec=True)
        patcher.start()
        self.addCleanup(patcher.stop)

        mock_github.get_organization().get_outside_collaborators.return_value = [{"login": "tom-smith"},
                                                                                 {"login": "john.smith"}]

        github_service = GithubService("", "moj-analytical-services")

        response = github_service.get_outside_collaborators_login_names()
        self.assertEqual(["tom-smith", "john.smith"], response)
        mock_github.get_organization.assert_has_calls(
            [call(), call('moj-analytical-services'), call().get_outside_collaborators()])

        patcher.stop()


if __name__ == "__main__":
    unittest.main()
