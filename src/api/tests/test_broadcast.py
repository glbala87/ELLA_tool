import datetime
import pytz
from vardb.datamodel import user, broadcast


def test_broadcast(test_database, session, client):

    test_database.refresh()

    # Test inital response being empty
    response = client.get('/api/v1/broadcasts/')
    assert response.json == []

    # Insert a broadcast
    now = datetime.datetime.now(pytz.utc)
    b1 = broadcast.Broadcast(
        message='Test',
        active=True,
        date_created=now
    )
    session.add(b1)
    session.commit()
    response = client.get('/api/v1/broadcasts/')
    assert response.json == [
        {
            'id': 1,
            'message': u'Test',
            'date': now.isoformat()
        }
    ]

    # Make it inactive

    b1.active = False
    session.commit()
    response = client.get('/api/v1/broadcasts/')
    assert response.json == []

    # Set expiry date for user 3 days from now
    # Client logs in as testuser1 by default
    expiry_date = now + datetime.timedelta(days=3)
    client_user = session.query(user.User).filter(
        user.User.username == 'testuser1'
    ).one()
    client_user.password_expiry = expiry_date
    session.commit()

    response = client.get('/api/v1/broadcasts/')
    assert response.json[0]['message'] == '''Your password will expire in 2 day(s). You may change it at any time by logging out and using "Change password"'''
