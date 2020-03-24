# Demo

To have a quick look at ELLA and how it works, you can easily bring up a demo instance if you have Docker installed. Simply run:

``` bash
make demo
```

This will start a demo instance populated with dummy test data at http://localhost:3114. 

::: warning NOTE
The demo instance lacks an annotation service and does not have data import functionality or the possibility to add attachments. 
:::

## Users 

There are several test users `testuser1`...`testuser8`, all with password `demo`. These are placed in different user groups, with access to different samples, UI setups and filter configurations: 

Group   |   Users   |   Access to
:---    |   :---   |    :---
1   |   `testuser1`–`testuser3` |   Small gene panels, VARIANTS and ANALYSES
2   |   `testuser4`–`testuser6` |   Large gene panels, ANALYSES only
3   |   `testuser7`–`testuser8` |   All gene panels, ANALYSES only

## Stop demo

To stop the demo instance, run:

``` bash
make kill-demo
```

