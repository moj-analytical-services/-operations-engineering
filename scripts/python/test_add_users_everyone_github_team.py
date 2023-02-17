import sys
import unittest
from unittest.mock import patch

from github import Github
from gql import Client
from gql.transport.aiohttp import AIOHTTPTransport

import add_users_everyone_github_team


@patch.object(Github, "__new__")
@patch.object(AIOHTTPTransport, "__new__")
@patch.object(Client, "__new__")
class TestAddUsersEveryoneGithubTeam(unittest.TestCase):

    def test_main_smoke_test(self, mock1, mock2, mock3):
        sys.argv = ["", "test"]
        add_users_everyone_github_team.main()

    def test_main_returns_error_when_no_token_provided(self, mock1, mock2, mock3):
        self.assertRaises(ValueError, add_users_everyone_github_team.main)


if __name__ == "__main__":
    unittest.main()
