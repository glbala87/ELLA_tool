# Testing

[[toc]]

## Types of tests

### End-to-end
A complete app with frontend and backend is started. Several use-cases
 are executed through the browser simulating a user clicking and entering text.
 The tests are written in Javascript and executed using [webdriverIO] (http://webdriver.io/).

### Unit tests
Testing of isolated Javascript or Python functions.

### API and integration tests
A database instance and the python backend is started. Tests written in Python
use the API and/or database to test various scenarios.

The tests are run twice, once against current database schema and once again where the database schema has been migrated from baseline to current.

## Running whole test suites

Remember to run `make test-build` before executing tests everytime you make changes.

- `make test` will run most test types apart from e2e.
- `make test-{type}` will run the different types of test.


## During development


### Python

If you want to run a specific API test while developing, you can enter your development container and run `source /ella/ops/dev/setup-local-integration-test.source`, before running the test with `py.test`. This script will tell the test framework to use your local database dump after the initial run, saving you a lot of time when running the test again.

The database fixtures are setup in different `conftest.py` files.

For normal unit testing, just run `py.test <path>` like normal.


### Javascript

You can run `yarn test-watch` inside the container to watch for changes.


### End to end testing (e2e)
We use webdriver.io for testing. See <http://webdriver.io>.

In CI tests are run with `make e2e-test`. This will run Chrome inside the container and run the test suites.
You can run this locally to check that the tests are passing, but it's unsuitable for authoring/editing tests.

To explore the e2e test data, start a local ELLA instance and import the e2e test data: `make dbreset TESTSET=e2e`


#### Local e2e
The following must be installed:
- Chrome
- Chromedriver

The ELLA app and the test execution (wdio) can be either run locally on your host machine or inside Docker: 

1. Start chromedriver on your host machine: 
    ``` bash
    ./chromedriver  --port=4444 --whitelisted-ips= --url-base ''
    ```
2. Start the tests: 
    ``` bash
    make e2e-test-local [options]
    ```

This will connect to the locally running Chromedriver and run one or several test specs. You'll see a local chrome browser where a "ghost" will click and enter text.

You can put debug statements (`browser.debug()`) in your test spec to have the test execution stop and enter a REPL to interact with the
browser. You can also open the dev tools in Chrome to dig around. Exit the REPL to have the test continue.

Relevant [`options`] for the `make` command:
Option|Explanation
:--|:--
`DEBUG=true` | Will make the browser visible (as opposed to headless), and increase test timeouts
`CHROME_HOST` | The IP address where the chromedriver is running. This will start a Chrome browser.
`SPEC="\<path to test>"` | Add this to run only a single/few tests. They must given as `src/webui/tests/e2e/tests/..` (comma separated if multiple).
`APP_URL` | URL of the app to test, e.g `http://localhost:8001`. Make sure to use an ip/port that is accessible from within the container where the tests themselves are running. If not defined, the app running inside container of the test execution is used.

::: warning NOTE
Maximize the Chrome window to reduce the number of 'element-not-clickable' errors.
:::

##### Misc

The best way to get and test selectors in Chrome is to use the [CSS Selector Helper for Chrome](https://chrome.google.com/webstore/detail/css-selector-helper-for-c/gddgceinofapfodcekopkjjelkbjodin) extension. Another way is to use the search (`Ctrl+F`) functionality in the Developer Tools to test your selector.

You can connect a debugger to Node.js instance on port `5859` to play around.

Use `browser.debug()` in a test file to pause the execution of the tests. This will present a REPL (webdriverio >= 4.5.0) where can you interact with webdriverio client to try out various commands, like `browser.element(...)`. It's also useful to head over to the browser's console to experiment and inspect variables.

Hit `Ctrl-C` in the REPL to continue the test run. See more on <http://webdriver.io/guide/usage/repl.html>

More info at <http://webdriver.io/guide/testrunner/debugging.html>
