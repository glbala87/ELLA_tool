# Testing

Types of tests: javascript, api/backend, database migration, end-to-end

## End-to-end
A complete app with frontend and backend is started. Several use-cases
 are executed through the browser simulating a user clicking and entering text.
 The tests are written in Javascript and executed using [webdriverIO] (http://webdriver.io/).
  
## Javascript  
Testing of isolated Javascript functions.
Written in Javascript, using the frameworks ...


## API/Backend
A database instance and the python backend is started. Tests written in Python
use the API to test various scenarios.

###############################################

Our test suites are intended to be run inside Docker. The Makefile has commands to do run setup and the tests themselves.

## Getting started
- `make test` will run most test types apart from e2e.
- `make test-{type}` will run the different types of test.

## Specific test

If you want to run a specific API test while developing, you can enter the docker container and run `source /ella/ops/dev/setup-local-integration-test.source`. This script will tell the test framework to use your local database dump after the initial run, saving you a lot of time when running the test again.

## End to end testing (e2e)
We use webdriver.io for testing. See <http://webdriver.io>.

In CI tests are run with `make e2e-test`. This will run Chrome in it's own container and run the test suites.
You can run this locally to check that the tests are passing, but it's unsuitable for authoring/editing tests.

To explore the e2e test data, start a local *ella* instance and import the e2e test data: `.../reset?testset=e2e`


## Local usage, REPL and debugging
The following must be installed:
- Chrome
- Chromedriver

The *ella* app and the test execution (wdio) can be either run locally on your host machine or inside Docker.

First start chromedriver on your host machine: `./chromedriver  --port=4444 --whitelisted-ips= --url-base ''`

Then start the tests: `make e2e-test-local ..options..`

It will connect to the locally running Chromedriver and run one or several test specs.
You'll see a local chrome browser where a "ghost" will click and enter text.

You can put debug statements  (browser.debug())in your test spec to have the test execution stop and enter a REPL to interact with the
browser. You can also open the dev tools in Chrome to dig around. Exit the REPL to have the test continue.

The relevant options to the make command:
- DEBUG=true (Will make the browser visible (as opposed to headless), and increase test timeouts)
- CHROME_HOST=.. the IP address where chromedriver is running. This will start a Chrome browser.
- Add SPEC="\<path to test>" to run only a single/few tests. They must given as src/webui/tests/e2e/tests/.. (comma separated if multiple).
- APP_URL: url of the app to test, like <http://localhost:8001>. Make sure to use an ip/port that is accessible from within the container where the tests themselves are running.
  If not defined the app running inside container of the test execution is used.

Maximize the Chrome window to reduce the number of 'element-not-clickable' errors.

Note! Make sure the versions of Chrome and Chromedriver are compatible

Maximize the Chrome window to reduce the number of 'element-not-clickable' errors.
Of course you need to have instellad the webdriverio Node module.

### Installing

Chromedriver:
- brew info chromedriver
- or <https://sites.google.com/a/chromium.org/chromedriver/downloads>

### Misc

Best way to get and test selectors in Chrome is to use the `CSS Selector Helper for Chrome` extension.
Another way is to use the search (`Ctrl+F`) functionality in the Developer Tools to test your selector.

You can connect a debugger to Node.js instance on port `5859` to play around.

Use `browser.debug()` in a test file to pause the execution of the tests. It will present a REPL (webdriverio >= 4.5.0) where can you interact with webdriverio client to try out various commands, like `browser.element(...)`. It's also useful to head over to the browser's console to experiment and inspect variables.

Hit 'Ctrl-c' in the REPL to continue the test run. See more on <http://webdriver.io/guide/usage/repl.html>

More info at <http://webdriver.io/guide/testrunner/debugging.html>
 