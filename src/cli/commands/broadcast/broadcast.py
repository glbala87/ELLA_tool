import click
from vardb.datamodel import broadcast as broadcast_model
from cli.decorators import cli_logger, session


@click.group(help="Broadcast")
def broadcast():
    pass


@broadcast.command("list", help="List all active messages")
@click.option("--all", is_flag=True, default=False, help="List all messages")
@click.option("--tail", is_flag=True, default=False, help="List last 10 messages")
@session
def cmd_list_active(session, all, tail):
    """
    Print all active broadcast messages to console
    """

    if tail:
        all = True

    filters = []
    if not all:
        filters.append(broadcast_model.Broadcast.active.is_(True))
    messages = session.query(broadcast_model.Broadcast)

    if filters:
        messages = messages.filter(*filters)

    if not filters and tail:
        messages = messages.order_by(broadcast_model.Broadcast.date_created.desc()).limit(10)

    messages = messages.all()

    if tail:
        messages.reverse()

    row_format = " {id:^5} | {date_created:^33} | {active:<10} | {message:<80} |"

    if messages:
        click.echo(
            row_format.format(id="id", date_created="date", active="active", message="message")
        )
        click.echo(
            row_format.format(id="-" * 5, date_created="-" * 33, active="-" * 10, message="-" * 80)
        )
        for msg in messages:
            click.echo(
                row_format.format(
                    id=msg.id,
                    date_created=msg.date_created.isoformat(),
                    active="true" if msg.active else "false",
                    message=msg.message,
                )
            )
    else:
        click.echo("No messages")


@broadcast.command("new", help="Create new message. Activated immediately.")
@click.argument("message", nargs=-1, type=click.UNPROCESSED)
@session
@cli_logger()
def cmd_new_message(logger, session, message):
    message = " ".join(message)

    if not message:
        logger.echo("Message empty")
        return

    new_message = broadcast_model.Broadcast(message=message, active=True)
    session.add(new_message)
    session.commit()

    logger.echo("Message with id {} added".format(new_message.id))


@broadcast.command("deactivate", help="Deactivate a message.")
@click.argument("message_id", type=click.INT)
@session
@cli_logger()
def cmd_deactivate_message(logger, session, message_id):
    message = (
        session.query(broadcast_model.Broadcast)
        .filter(broadcast_model.Broadcast.id == message_id)
        .one_or_none()
    )

    if not message:
        logger.echo("Found no message with id {}".format(message_id))
        return

    message.active = False
    session.commit()
    logger.echo("Message with id {} set as inactive".format(message.id))
