import getpass
import sys
import logging
from functools import update_wrapper
import click

from vardb.util import DB
from vardb.datamodel import log

logging.basicConfig(level=logging.INFO)


class CliLogger(object):
    def __init__(self, ctx):
        self.ctx = ctx
        self.echoed = list()
        self.log = log.CliLog()
        user = getpass.getuser()
        if not user:
            raise RuntimeError(
                "Couldn't find your system username. A username is required for auditing purposes."
            )
        self.log.user = user

    def echo(self, message, db_only=False):
        self.echoed.append(message)
        if not db_only:
            click.echo(message)

    def exception(self, message):
        logging.exception(message)

    def commit(self):
        group = ""
        if self.ctx.parent and self.ctx.parent.command:
            group = self.ctx.parent.command.name
        self.log.group = group
        self.log.groupcommand = self.ctx.command.name
        self.log.output = "\n".join(self.echoed)
        self.log.command = " ".join(sys.argv[1:])

        db = DB()
        db.connect()
        session = db.session
        session.add(self.log)
        session.commit()
        db.disconnect()


def cli_logger(f):
    """Decorator for logging cli commands to database.
    """

    def new_func(*args, **kwargs):
        ctx = click.get_current_context()
        if not getattr(ctx, "clilogger", None):
            ctx.clilogger = CliLogger(ctx)
        try:
            result = f(ctx.clilogger, *args, **kwargs)
            return result
        finally:
            ctx.clilogger.commit()

    return update_wrapper(new_func, f)


def session(f):
    """Decorator providing a database session.
    """

    def new_func(*args, **kwargs):
        ctx = click.get_current_context()
        if not getattr(ctx, "session", None):
            db = DB()
            db.connect()
            ctx.db = db
            ctx.session = db.session
        try:
            return f(ctx.session, *args, **kwargs)
        finally:
            ctx.db.disconnect()

    return update_wrapper(new_func, f)
