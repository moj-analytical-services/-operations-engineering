import sys
import time
import traceback

from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
from graphql import DocumentNode

from services.GithubService import GithubService


def print_stack_trace(message):
    """Print a stack trace when an exception occurs

    Args:
        message (string): A message to print when exception occurs
    """
    print(message)
    try:
        exc_info = sys.exc_info()
    finally:
        traceback.print_exception(*exc_info)
        del exc_info


def repository_user_names_query(after_cursor=None, repository_name=None) -> DocumentNode:
    """A GraphQL query to get the list of user names within a repository that have direct access.

    Args:
        after_cursor (string, optional): Is the pagination offset value gathered from the previous API request. Defaults to None.
        repository_name (string, optional): Is the name of the repository that has the associated user/s. Defaults to None.

    Returns:
        gql: The GraphQL query result
    """
    query = """
    query {
        repository(name: REPOSITORY_NAME, owner: "moj-analytical-services") {
            collaborators(first: 100, after:AFTER, affiliation: DIRECT) {
                edges {
                    node {
                        login
                    }
                }
                pageInfo {
                    hasNextPage
                    endCursor
                }
            }
        }
    }
    """.replace(
        # This is the next page ID to start the fetch from
        "AFTER",
        '"{}"'.format(after_cursor) if after_cursor else "null",
    ).replace(
        "REPOSITORY_NAME",
        '"{}"'.format(repository_name) if repository_name else "null",
    )

    return gql(query)


def organisation_repo_name_query(after_cursor=None) -> DocumentNode:
    """A GraphQL query to get the list of organisation repo names

    Args:
        after_cursor (string, optional): Is the pagination offset value gathered from the previous API request. Defaults to None.

    Returns:
        gql: The GraphQL query result
    """
    query = """
    query {
        organization(login: "moj-analytical-services") {
            repositories(first: 100, after:AFTER) {
                pageInfo {
                    endCursor
                    hasNextPage
                }
                edges {
                    node {
                        name
                        isDisabled
                        isArchived
                        isLocked
                        hasIssuesEnabled
                    }
                }
            }
        }
    }
        """.replace(
        # This is the next page ID to start the fetch from
        "AFTER",
        '"{}"'.format(after_cursor) if after_cursor else "null",
    )

    return gql(query)


def organisation_teams_name_query(after_cursor=None) -> DocumentNode:
    """A GraphQL query to get the list of organisation team names

    Args:
        after_cursor (string, optional): Is the pagination offset value gathered from the previous API request. Defaults to None.

    Returns:
        gql: The GraphQL query result
    """
    query = """
    query {
        organization(login: "moj-analytical-services") {
            teams(first: 100, after:AFTER) {
                pageInfo {
                    endCursor
                    hasNextPage
                }
                edges {
                    node {
                        slug
                    }
                }
            }
        }
    }
        """.replace(
        # This is the next page ID to start the fetch from
        "AFTER",
        '"{}"'.format(after_cursor) if after_cursor else "null",
    )

    return gql(query)


def organisation_team_id_query(team_name=None) -> DocumentNode:
    """A GraphQL query to get the id of an organisation team

    Args:
        team_name (string, optional): Name of the organisation team. Defaults to None.

    Returns:
        gql: The GraphQL query result
    """
    query = """
    query {
        organization(login: "moj-analytical-services") {
            team(slug: TEAM_NAME) {
                databaseId
            }
        }
    }
        """.replace(
        # This is the team name
        "TEAM_NAME",
        '"{}"'.format(team_name) if team_name else "null",
    )

    return gql(query)


def team_repos_query(after_cursor=None, team_name=None) -> DocumentNode:
    """A GraphQL query to get the list of repos a team has access to in the organisation

    Args:
        after_cursor (string, optional): Is the pagination offset value gathered from the previous API request. Defaults to None.
        team_name (string, optional): Is the name of the team that has the associated repo/s. Defaults to None.

    Returns:
        gql: The GraphQL query result
    """
    query = """
    query {
        organization(login: "moj-analytical-services") {
            team(slug: TEAM_NAME) {
                repositories(first: 100, after:AFTER) {
                    edges {
                        node {
                            name
                        }
                    }
                    pageInfo {
                        endCursor
                        hasNextPage
                    }
                }
            }
        }
    }
    """.replace(
        # This is the next page ID to start the fetch from
        "AFTER",
        '"{}"'.format(after_cursor) if after_cursor else "null",
    ).replace(
        "TEAM_NAME",
        '"{}"'.format(team_name) if team_name else "null",
    )

    return gql(query)


def team_user_names_query(after_cursor=None, team_name=None) -> DocumentNode:
    """A GraphQL query to get the list of user names within each organisation team.

    Args:
        after_cursor (string, optional): Is the pagination offset value gathered from the previous API request. Defaults to None.
        team_name (string, optional): Is the name of the team that has the associated user/s. Defaults to None.

    Returns:
        gql: The GraphQL query result
    """
    query = """
    query {
        organization(login: "moj-analytical-services") {
            team(slug: TEAM_NAME) {
                members(first: 100, after:AFTER) {
                    edges {
                        node {
                            login
                        }
                    }
                    pageInfo {
                        hasNextPage
                        endCursor
                    }
                }
            }
        }
    }
    """.replace(
        # This is the next page ID to start the fetch from
        "AFTER",
        '"{}"'.format(after_cursor) if after_cursor else "null",
    ).replace(
        "TEAM_NAME",
        '"{}"'.format(team_name) if team_name else "null",
    )

    return gql(query)


def fetch_repo_names(gql_client: Client, repo_issues_enabled) -> list:
    """A wrapper function to run a GraphQL query to get the list of repo names in the organisation

    Returns:
        list: A list of the organisation repos names
    """
    has_next_page = True
    after_cursor = None
    repo_name_list = []

    while has_next_page:
        query = organisation_repo_name_query(after_cursor)

        try:
            data = gql_client.execute(query)
        except Exception as err:
            print("Exception in fetch_repo_names()")
            print(err)
        else:
            # Retrieve the name of the repos
            if data["organization"]["repositories"]["edges"] is not None:
                for repo in data["organization"]["repositories"]["edges"]:
                    # Skip locked repositories
                    if not (
                        repo["node"]["isDisabled"]
                        or repo["node"]["isArchived"]
                        or repo["node"]["isLocked"]
                    ):
                        repo_name_list.append(repo["node"]["name"])
                        repo_issues_enabled[repo["node"]["name"]] = repo["node"][
                            "hasIssuesEnabled"
                        ]

            # Read the GH API page info section to see if there is more data to read
            has_next_page = data["organization"]["repositories"]["pageInfo"]["hasNextPage"]
            after_cursor = data["organization"]["repositories"]["pageInfo"]["endCursor"]

    return repo_name_list


def fetch_repository_users(gql_client: Client, repository_name: str, outside_collaborators: list[str]) -> list:
    """A wrapper function to run a GraphQL query to get the list of users within an repository with direct access

    Args:
        repository_name (string): Is the repository within the organisation to check

    Returns:
        list: A list of the repository user names
    """
    has_next_page = True
    after_cursor = None
    repository_user_name_list = []

    while has_next_page:
        query = repository_user_names_query(after_cursor, repository_name)

        try:
            data = gql_client.execute(query)
        except Exception as err:
            print("Exception in fetch_repository_users()")
            print(err)
        else:
            # Retrieve the usernames of the repository members
            if data["repository"]["collaborators"]["edges"] is not None:
                for repository in data["repository"]["collaborators"]["edges"]:
                    # Ignore users that are outside collaborators
                    if repository["node"]["login"] not in outside_collaborators:
                        repository_user_name_list.append(
                            repository["node"]["login"])

            # Read the GH API page info section to see if there is more data to read
            has_next_page = data["repository"]["collaborators"]["pageInfo"]["hasNextPage"]
            after_cursor = data["repository"]["collaborators"]["pageInfo"]["endCursor"]

    return repository_user_name_list


def fetch_team_names(gql_client: Client) -> list:
    """A wrapper function to run a GraphQL query to get the list of teams in the organisation

    Returns:
        list: A list of the organisation team names
    """
    has_next_page = True
    after_cursor = None
    team_name_list = []

    while has_next_page:
        query = organisation_teams_name_query(after_cursor)
        try:
            data = gql_client.execute(query)
        except Exception as err:
            print("Exception in fetch_team_names()")
            print(err)
        else:
            # Retrieve the name of the teams
            if data["organization"]["teams"]["edges"] is not None:
                for team in data["organization"]["teams"]["edges"]:
                    team_name_list.append(team["node"]["slug"])

            # Read the GH API page info section to see if there is more data to read
            has_next_page = data["organization"]["teams"]["pageInfo"]["hasNextPage"]
            after_cursor = data["organization"]["teams"]["pageInfo"]["endCursor"]

    return team_name_list


def fetch_team_id(gql_client: Client, team_name) -> int:
    """A wrapper function to run a GraphQL query to get the team ID

    Args:
        team_name (string): The team name

    Returns:
        int: The team ID of the team
    """
    query = organisation_team_id_query(team_name)
    try:
        data = gql_client.execute(query)
    except Exception as err:
        print("Exception in fetch_team_id()")
        print(err)
    else:
        if (
            data["organization"]["team"]["databaseId"] is not None
            and data["organization"]["team"]["databaseId"]
        ):
            return data["organization"]["team"]["databaseId"]
    return 0


def fetch_team_users(gql_client: Client, team_name) -> list:
    """A wrapper function to run a GraphQL query to get the list of users within an organisation team

    Args:
        team_name (string): Is the team within the organisation to check

    Returns:
        list: A list of the team user names
    """
    has_next_page = True
    after_cursor = None
    team_user_name_list = []

    while has_next_page:
        query = team_user_names_query(after_cursor, team_name)
        try:
            data = gql_client.execute(query)
        except Exception as err:
            print("Exception in fetch_team_users()")
            print(err)
        else:
            # Retrieve the usernames of the team members
            if data["organization"]["team"]["members"]["edges"] is not None:
                for team in data["organization"]["team"]["members"]["edges"]:
                    team_user_name_list.append(team["node"]["login"])

            # Read the GH API page info section to see if there is more data to read
            has_next_page = data["organization"]["team"]["members"]["pageInfo"][
                "hasNextPage"
            ]
            after_cursor = data["organization"]["team"]["members"]["pageInfo"]["endCursor"]

    return team_user_name_list


def fetch_team_repos(gql_client: Client, team_name) -> list:
    """A wrapper function to run a GraphQL query to get the list of repo within in an organisation team

    Args:
        team_name (string): Is the team within the organisation to check

    Returns:
        list: A list of team repo names
    """
    has_next_page = True
    after_cursor = None
    team_repo_list = []

    while has_next_page:
        query = team_repos_query(after_cursor, team_name)
        try:
            data = gql_client.execute(query)
        except Exception as err:
            print("Exception in fetch_team_repos()")
            print(err)
        else:
            # Retrieve the name of the teams repos
            if data["organization"]["team"]["repositories"]["edges"] is not None:
                for team in data["organization"]["team"]["repositories"]["edges"]:
                    team_repo_list.append(team["node"]["name"])

            # Read the GH API page info section to see if there is more data to read
            has_next_page = data["organization"]["team"]["repositories"]["pageInfo"][
                "hasNextPage"
            ]
            after_cursor = data["organization"]["team"]["repositories"]["pageInfo"][
                "endCursor"
            ]

    return team_repo_list


class Repository:
    """A struct to store repository info ie name and users"""

    name: str
    direct_members: list

    def __init__(self, x, y):
        self.name = x
        self.direct_members = y


def fetch_repository(gql_client: Client, repository_name, outside_collaborators: list[str]) -> Repository:
    """Fetches the repository info from GH

    Args:
        repository_name (string): Name of the repository

    Returns:
        Repository: A repository object
    """
    repository_users_list = fetch_repository_users(
        gql_client, repository_name, outside_collaborators)
    return Repository(repository_name, repository_users_list)


def fetch_repositories(gql_client: Client, outside_collaborators: list[str], repo_issues_enabled) -> list:
    """Wrapper function to retrieve the repositories info ie name, users

    Returns:
        list: A list that contains all the repositories data ie name, users
    """
    repositories_list = []
    repository_names_list = fetch_repo_names(gql_client, repo_issues_enabled)
    for repository_name in repository_names_list:
        repositories_list.append(fetch_repository(
            gql_client, repository_name, outside_collaborators))

    return repositories_list


class team:
    """A struct to store team info ie name, users, repos, GH ID"""

    name: str
    team_users: list
    team_repositories: list
    team_id: int

    def __init__(self, a, b, c, d):
        self.name = a
        self.team_users = b
        self.team_repositories = c
        self.team_id = d


def fetch_team(gql_client: Client, team_name) -> team:
    """Fetches the team info from GH

    Args:
        team_name (string): Name of the team

    Returns:
        team: A team object
    """
    team_users_list = fetch_team_users(gql_client, team_name)
    team_repos_list = fetch_team_repos(gql_client, team_name)
    team_id = fetch_team_id(gql_client, team_name)
    return team(team_name, team_users_list, team_repos_list, team_id)


def fetch_teams(gql_client: Client) -> list:
    """Wrapper function to retrieve the organisation team info ie name, users, repos

    Returns:
        list: A list that contains all the organisation teams data ie name, users, repos
    """
    teams_list = []
    teams_names_list = fetch_team_names(gql_client)
    for team_name in teams_names_list:
        teams_list.append(fetch_team(gql_client, team_name))
        # Delay for GH API
        time.sleep(1)

    return teams_list


def remove_users_with_duplicate_access(github_service: GithubService, repo_issues_enabled,
                                       repository_name, repository_direct_users, users_not_in_a_team, org_teams
                                       ):
    """Check which users have access to the repo through a team
    and direct access and remove their direct access permission.

    Args:
        repository_name (string): the name of the repository
        repository_direct_users (list): user names of the repositories users
        users_not_in_a_team (list): a duplicate list of the repositories users
        org_teams (list): a list of the organizations teams
    """
    previous_user = ""
    previous_repository = ""

    # loop through each repository direct users
    for username in repository_direct_users:
        # loop through all the organisation teams
        for team in org_teams:
            # see if that team is attached to the repository and contains the direct user
            if (repository_name in team.team_repositories) and (
                username in team.team_users
            ):
                # This check helps skip duplicated results
                if (username != previous_user) and (
                    repository_name != previous_repository
                ):
                    # raise an issue to say the user has been removed and has access via the team
                    if repo_issues_enabled.get(repository_name, repo_issues_enabled):
                        github_service.create_an_access_removed_issue_for_user_in_repository(username,
                                                                                             repository_name)

                    # remove the direct user from the repository
                    github_service.remove_user_from_repository(
                        username, repository_name)

                    # save values for next iteration
                    previous_user = username
                    previous_repository = repository_name

                    # The user is in a team
                    users_not_in_a_team.remove(username)


def get_user_permission(github_service: GithubService, repository_name, username):
    """gets the user permissions for a repository

    Args:
        repository_name (string): the name of the repository
        username (string): the name of the user

    Returns:
        string: the user permission level
    """
    users_permission = None

    try:
        gh = github_service.client
        repo = gh.get_repo(
            f"{github_service.organisation_name}/{repository_name}")
        user = gh.get_user(username)
        users_permission = repo.get_collaborator_permission(user)
    except Exception:
        message = "Warning: Exception getting the users permission " + username
        print_stack_trace(message)

    return users_permission


def remove_user_from_team(github_service: GithubService, team_id, username):
    """remove a user from a team

    Args:
        team_id (int): the GH ID of the team
        username (string): the name of the user
    """
    try:
        gh = github_service.client
        org = gh.get_organization("moj-analytical-services")
        gh_team = org.get_team(team_id)
        user = gh.get_user(username)
        gh_team.remove_membership(user)
        # Delay for GH API
        time.sleep(5)
        print("Remove user " + username + " from team " + team_id.__str__())
    except Exception:
        message = (
            "Warning: Exception in removing user "
            + username
            + " from team "
            + team_id.__str__()
        )
        print_stack_trace(message)


def add_user_to_team(github_service: GithubService, team_id, username):
    """add a user to a team

    Args:
        team_id (int): the GH ID of the team
        username (string): the name of the user
    """
    try:
        gh = github_service.client
        org = gh.get_organization("moj-analytical-services")
        gh_team = org.get_team(team_id)
        user = gh.get_user(username)
        gh_team.add_membership(user)
        # Delay for GH API
        time.sleep(5)
        print("Add user " + username + " to team " + team_id.__str__())
    except Exception:
        message = (
            "Warning: Exception in adding user "
            + username
            + " to team "
            + team_id.__str__()
        )
        print_stack_trace(message)


def create_new_team_with_repository(github_service: GithubService, repository_name, team_name):
    """create a new team and attach to a repository

    Args:
        repository_name (string): the name of the repository to attach to
        team_name (string): the name of the team
    """
    try:
        gh = github_service.client
        repo = gh.get_repo(
            f"{github_service.organisation_name}/{repository_name}")
        org = gh.get_organization("moj-analytical-services")
        org.create_team(
            team_name,
            [repo],
            "",
            "closed",
            "Automated generated team to grant users access to this repository",
        )
        # Delay for GH API
        time.sleep(5)
        print("Creating new team " + team_name)
    except Exception:
        message = "Warning: Exception in creating a team " + team_name
        print_stack_trace(message)


def does_team_exist(github_service: GithubService, team_name):
    """Check if a team exists in the organization

    Args:
        team_name (string): the name of the team

    Returns:
        bool: if the team was found in the organization
    """

    team_found = False

    try:
        gh = github_service.client
        org = gh.get_organization("moj-analytical-services")
        gh_teams = org.get_teams()
        for gh_team in gh_teams:
            if gh_team.name == team_name:
                team_found = True
                break
    except Exception:
        message = "Warning: Exception in check to see if a team exists " + team_name
        print_stack_trace(message)

    return team_found


def change_team_repository_permission(github_service: GithubService, repository_name, team_name, team_id, permission):
    """changes the team permissions on a repository

    Args:
        repository_name (string): the name of the repository
        team_name (string): the name of the team
        team_id (int): the GH id of the team
        permission (string): the permission of the team
    """
    if permission == "read":
        permission = "pull"
    elif permission == "write":
        permission = "push"

    try:
        gh = github_service.client
        repo = gh.get_repo(
            f"{github_service.organisation_name}/{repository_name}")
        org = gh.get_organization("moj-analytical-services")
        gh_team = org.get_team(team_id)
        gh_team.update_team_repository(repo, permission)
        # Delay for GH API
        time.sleep(5)
        print("Change team " + team_name + " repo permission to " + permission)
    except Exception:
        message = (
            "Warning: Exception in changing team "
            + team_name
            + " permission on repository "
            + repository_name
        )
        print_stack_trace(message)


def correct_team_name(team_name):
    """GH team names use a slug name. This
    swaps ., _, , with a - and lower cases
    the team name

    Args:
        team_name (string): the name of the team

    Returns:
        string: converted team name
    """
    temp_name = ""
    new_team_name = ""

    temp_name = team_name
    temp_name = temp_name.replace(".", "-")
    temp_name = temp_name.replace("_", "-")
    temp_name = temp_name.replace(" ", "-")
    temp_name = temp_name.replace("---", "-")
    temp_name = temp_name.replace("--", "-")

    if temp_name.startswith(".") or temp_name.startswith("-"):
        temp_name = temp_name[1:]

    if temp_name.endswith(".") or temp_name.endswith("-"):
        temp_name = temp_name[:-1]

    new_team_name = temp_name.lower()

    return new_team_name


def put_user_into_existing_team(
    github_service: GithubService, repository_name, username, users_not_in_a_team, org_teams
):
    """Put a user with direct access to a repository into an existing team

    Args:
        repository_name (string): the name of the repository
        username (string): the name of the user
        users_not_in_a_team (list): a list of the repositories users with direct access
        org_teams (list): a list of the organizations teams
    """

    if repository_name == "" or username == "" or len(org_teams) == 0:
        users_not_in_a_team.clear()
    elif len(users_not_in_a_team) == 0:
        pass
    else:
        users_permission = get_user_permission(
            github_service, repository_name, username)

        # create a team name that has the same permissions as the user
        temp_name = repository_name + "-" + users_permission + "-team"
        expected_team_name = correct_team_name(temp_name)

        # Find an existing team with the same permissions as
        # the user which has access to the repository
        for team in org_teams:
            if (expected_team_name == team.name) and (
                repository_name in team.team_repositories
            ):
                add_user_to_team(github_service, team.team_id, username)
                github_service.remove_user_from_repository(
                    username, repository_name)
                users_not_in_a_team.remove(username)


def put_users_into_new_team(github_service: GithubService, gql_client: Client, repository_name, remaining_users):
    """put users into a new team

    Args:
        repository_name (string): the name of the repository
        remaining_users (list): a list of user names that have direct access to the repository
    """
    team_id = 0

    if repository_name == "" or len(remaining_users) == 0:
        return
    else:
        for username in remaining_users:
            users_permission = get_user_permission(
                github_service, repository_name, username)

            temp_name = repository_name + "-" + users_permission + "-team"
            team_name = correct_team_name(temp_name)

            if not does_team_exist(github_service, team_name):
                create_new_team_with_repository(
                    github_service, repository_name, team_name)
                team_id = fetch_team_id(gql_client, team_name)
                # Depends who adds the oauth_token to repo is added to every team
                remove_user_from_team(github_service, team_id, "AntonyBishop")
                remove_user_from_team(github_service, team_id, "nickwalt01")
                remove_user_from_team(github_service, team_id, "ben-al")
                remove_user_from_team(github_service,
                                      team_id, "moj-operations-engineering-bot")

            team_id = fetch_team_id(gql_client, team_name)

            change_team_repository_permission(github_service,
                                              repository_name, team_name, team_id, users_permission
                                              )

            add_user_to_team(github_service, team_id, username)
            github_service.remove_user_from_repository(
                username, repository_name)


def run(github_service: GithubService, gql_client: Client, badly_named_repositories: list[str], repo_issues_enabled):
    """A function for the main functionality of the script"""

    # Get the usernames of the outside collaborators
    outside_collaborators = github_service.get_outside_collaborators_login_names()

    # Get the MoJ organisation teams and users info
    org_teams = fetch_teams(gql_client)

    # Get the MoJ organisation repos and direct users
    org_repositories = fetch_repositories(
        gql_client, outside_collaborators, repo_issues_enabled)

    # loop through each organisation repository
    for repository in org_repositories:

        if repository.name not in badly_named_repositories:
            # close any previously opened issues that have expired
            github_service.close_expired_issues(repository.name)

            users_not_in_a_team = repository.direct_members

            remove_users_with_duplicate_access(github_service, repo_issues_enabled,
                                               repository.name,
                                               repository.direct_members,
                                               users_not_in_a_team,
                                               org_teams,
                                               )

            remaining_users = users_not_in_a_team

            for username in users_not_in_a_team:
                put_user_into_existing_team(github_service,
                                            repository.name, username, remaining_users, org_teams
                                            )

            put_users_into_new_team(
                github_service, gql_client, repository.name, remaining_users)


def main():
    if len(sys.argv) == 2:
        # Get the GH Action token
        oauth_token = sys.argv[1]
    else:
        raise ValueError("Missing a script input parameter")

    github_service = GithubService(oauth_token, "moj-analytical-services")

    repo_issues_enabled = {}

    # Setup a transport and client to interact with the GH GraphQL API
    try:
        transport = AIOHTTPTransport(
            url="https://api.github.com/graphql",
            headers={"Authorization": "Bearer {}".format(oauth_token)},
        )
    except Exception:
        print_stack_trace("Exception: Problem with the API URL or GH Token")

    try:
        gql_client = Client(transport=transport,
                            fetch_schema_from_transport=False)
    except Exception:
        print_stack_trace("Exception: Problem with the Client.")
    badly_named_repositories = []
    print("Start")
    run(github_service, gql_client, badly_named_repositories, repo_issues_enabled)
    print("Finished")


if __name__ == "__main__":
    main()
