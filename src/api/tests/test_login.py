USER = "testuser3"
PASSWORD = "demo"


def test_login(client, test_database):
    test_database.refresh()  # Reset db
    data = {"username": USER, "password": PASSWORD}
    resp = client.post("/api/v1/users/actions/login/", data=data, username=None)
    assert resp.status_code == 302


def test_login_fails(client, test_database):
    test_database.refresh()  # Reset db
    wrong_password = "randompw"

    data = {"username": USER, "password": wrong_password}
    resp = client.post("/api/v1/users/actions/login/", data=data, username=None)
    assert resp.status_code == 401


def test_users_lock_incorrect_logins(client, test_database):
    test_database.refresh()  # Reset db
    wrong_password = "randompw"

    # Do 6 incorrect logins. This should lock the user.
    for i in range(6):
        data = {"username": USER, "password": wrong_password}
        resp = client.post("/api/v1/users/actions/login/", data=data, username=None)
        assert resp.status_code == 401

    # Attempting to log in with correct password should now fail
    data = {"username": USER, "password": PASSWORD}
    resp = client.post("/api/v1/users/actions/login/", data=data, username=None)
    assert resp.status_code == 401
    assert "Too many failed logins" in resp.get_data()

    # Check that user cannot change password after too many failed logins
    new_password = "NewPassword1234"
    data = {"username": USER, "password": PASSWORD, "new_password": new_password}
    resp = client.post("/api/v1/users/actions/changepassword/", data=data, username=None)
    assert resp.status_code == 401


def test_change_password(client, test_database):
    test_database.refresh()  # Reset db
    new_password = "NewPassword1234"
    data = {"username": USER, "password": PASSWORD, "new_password": new_password}
    resp = client.post("/api/v1/users/actions/changepassword/", data=data, username=None)

    assert resp.status_code == 200

    # Test login with new password
    data = {"username": USER, "password": new_password}
    resp = client.post("/api/v1/users/actions/login/", data=data, username=None)
    assert resp.status_code == 302
