import unittest
from unittest.mock import Mock, patch

from scripts.python.services.GithubService import GithubService


class TestGithubService(unittest.TestCase):
    mock_github = None

    def setUp(self):
        self.mock_github = Mock()
        self.patcher = patch(target='github.Github.__new__', return_value=self.mock_github)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def tearDown(self):
        self.patcher.stop()

    def test_innit_sets_up_class(self):
        github_service = GithubService('')
        self.assertIs(self.mock_github, github_service.client)


if __name__ == '__main__':
    unittest.main()
