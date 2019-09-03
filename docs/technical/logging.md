# Logging

There are currently two kinds of formal logging functionality in ELLA, API resource logging and command line logging.

In addition, you would normally store the log files from the ELLA processes as well. They also include an additional copy of all API requests made.

## API logging

All API resource requests are logged to the table `resourcelog`.

Note that some resources are exempted from detailed logging, for instance
requests that will contain password information or resources that
are part of data polling and therefore called at small intervals (provided
they're not considered important for auditing purposes).

The following information is stored per request:

- **Remote address** - IP address of the remote making the request
- **Time**
- **Duration** - Time it took to generate response
- **Usersession id** - what usersession made the request (if authenticated)
- **HTTP method**
- **Resource URI**
- **HTTP query parameters**
- **Response body** - POST/PATCH/DELETE only
- **Response body size** - in bytes
- **Payload body data** - POST/PATCH/DELETE only
- **Payload body size** - in bytes
- **HTTP response status code**

One can from this table create any kind of auditing information, e.g. what users have read or written to which analyses.

## CLI logging

Usage of `ella-cli` is logged to database table `clilog`.

The following information is stored:

- **Time**
- **User** - $USER from environment.
- **Group** - Group of command, e.g. `users`
- **Group command** - Group's subcommand, e.g. `reset_password`
- **Command** - Full command as entered on command line (from `sys.argv`)
- **Reason** - Some commands support providing a reason for running the command. Manually entered free text.
- **Output** - Does not contain whole stdout, just the relevant CLI parts.


::: warning NOTE
The system user running a command is primarily fetched from `$USER` environment variable, and can easily be spoofed.
:::
