import pytest
from vardb.datamodel import user
from api.util.useradmin import authenticate_user, generate_password, change_password, password_expired, get_user

def test_user_list(run_command):
    result = run_command(["users", "list"])
    assert result.exit_code == 0


def test_user_activity(session, run_command):
    result = run_command(["users", "activity"])
    assert result.exit_code == 0


@pytest.mark.parametrize("username", ["testuser1", "testuser2", "testuser3", "testuser4", "testuser5", "testuser6"])
def test_user_reset_password(test_database, session, run_command, username):
    test_database.refresh()
    result = run_command(["users", "reset_password", username])
    assert result.exit_code == 0
    password = result.output.replace('\n','').split(' ')[-1]
    assert password_expired(get_user(session, username))

    # Check that new password works
    new_password, _ = generate_password()
    change_password(session, username, password, new_password)
    authenticate_user(session, username, new_password)


@pytest.mark.parametrize("username", ["testuser1", "testuser2", "testuser3", "testuser4", "testuser5", "testuser6"])
def test_user_lock(session, username, run_command):
    result = run_command(["users", "lock", username])
    assert result.exit_code == 0
    u = session.query(user.User).filter(
        user.User.username == username,
        user.User.active.is_(False),
    ).one()


def test_user_modify(session, run_command):
    username = "testuser3"
    new_username = "werg3lla"
    first_name = "Jacobine Camilla"
    last_name = "Wergeland"

    result = run_command(["users", "modify", username, "--new_username", new_username, "--first_name", first_name, "--last_name", last_name])
    assert result.exit_code == 0

    old_user = session.query(
        user.User
    ).filter(
        user.User.username == username
    ).first()
    assert old_user is None

    session.query(
        user.User
    ).filter(
        user.User.username == new_username,
        user.User.first_name == first_name,
        user.User.last_name == last_name,
    ).one()


def test_user_add(session, run_command):
    username = "SaucySebastian"
    first_name = "Johan Sebastian"
    last_name = "Welhaven"
    usergroup = "testgroup01"

    result = run_command(["users", "add", "--username", username, "--first_name", first_name, "--last_name", last_name, "--usergroup", usergroup])
    assert result.exit_code == 0

    u = session.query(
        user.User
    ).filter(
        user.User.username == username,
    ).one()
    assert u.first_name == first_name
    assert u.last_name == last_name
    assert u.group.name == usergroup
