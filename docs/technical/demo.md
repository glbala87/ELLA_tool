# Demo

To have a quick look at ELLA and how it works, you can easily bring up a demo instance if you have
Docker installed. The database is pre-loaded with analyses and variants and users with different
roles and configurations. Details on the test data are available in the
[alleles/ella-testdata](https://gitlab.com/alleles/ella-testdata.git) repo.

<!-- Is this still true? -->
::: warning NOTE
The demo instance lacks an annotation service and does not have data import functionality or the possibility to add attachments.
:::

## Starting the demo instance

Several `make options` are available depending on which image you would like to use. The two most useful are:

```bash
# use the latest tagged release
make demo-release

# use the latest dev image (may be unstable)
make demo-dev
```

See the `Makefile` for other, more specific use cases.

## Using the demo instance

Once the demo is started the URL to the instance is printed on the terminal. The default is <http://localhost:3114>.

It is possible to adjust various settings (such as the port) by passing arguments to `make`. _e.g.,_

> `$ make demo-release DEMO_HOST_PORT=8080`
>
> `...`
>
> `Demo is now running at http://localhost:8080. Some example user/pass are testuser1/demo and testuser5/demo.`

Check the Makefile for a full list of the `DEMO_*` variables and to see how they are used.

### Users

There are several test users `testuser1`...`testuser8`, all with password `demo`. These are placed
in different user groups, with access to different samples, UI setups and filter configurations:

| Group | Users                   | Access to                                |
| :---- | :---------------------- | :--------------------------------------- |
| 1     | `testuser1`–`testuser3` | Small gene panels, VARIANTS and ANALYSES |
| 2     | `testuser4`–`testuser6` | Large gene panels, ANALYSES only         |
| 3     | `testuser7`–`testuser8` | All gene panels, ANALYSES only           |

## Stop demo

To stop the demo instance, run:

``` bash
make kill-demo
```
