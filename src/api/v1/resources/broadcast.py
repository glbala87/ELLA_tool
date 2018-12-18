import logging
import uuid
import datetime
import pytz
from vardb.datamodel import user as user_model, broadcast

from api import schemas, ApiError

from api.v1.resource import LogRequestResource

# from flask import Response, make_response, redirect, request
from api.util.util import authenticate


log = logging.getLogger(__name__)


PASSWORD_NOTICE_DAYS = 7


class BroadcastResource(LogRequestResource):
    @authenticate(optional=True)
    def get(self, session, user=None):
        """
        Returns a list of messages. Include personal ones if user is defined.
        ---
        summary: Broadcast messages
        tags:
          - Message
        """

        messages = list()

        if user:
            expire_date = datetime.datetime.now(pytz.utc) + datetime.timedelta(
                days=PASSWORD_NOTICE_DAYS
            )
            password_expiry = (
                session.query(user_model.User.password_expiry)
                .filter(
                    user_model.User.id == user.id, user_model.User.password_expiry < expire_date
                )
                .scalar()
            )

            if password_expiry:
                days_delta = (password_expiry - datetime.datetime.now(pytz.utc)).days
                messages.append(
                    {
                        "id": uuid.uuid4().get_hex(),
                        "message": 'Your password will expire in {} day(s). You may change it at any time by logging out and using "Change password"'.format(
                            days_delta
                        ),
                        "date": (
                            password_expiry - datetime.timedelta(days=PASSWORD_NOTICE_DAYS)
                        ).isoformat(),
                    }
                )

        db_messages = (
            session.query(broadcast.Broadcast)
            .filter(broadcast.Broadcast.active.is_(True))
            .order_by(broadcast.Broadcast.date_created)
            .all()
        )

        for db_message in db_messages:
            messages.append(
                {
                    "id": db_message.id,
                    "date": db_message.date_created.isoformat(),
                    "message": db_message.message,
                }
            )

        return messages
