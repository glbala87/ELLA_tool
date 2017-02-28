const DEBUG = process.env.DEBUG;

/**
 * Utilities for logging and working with the WebdriverIO API.
 */
class Util {

    logSelector(selector, debug=DEBUG) {
        if (debug) {
            console.log(`Finding element using selector '${selector}'`)
        }
    }

    log(msg, debug=DEBUG) {
        if (debug) {
            console.log(msg);
        }
    }

    elementOrNull(selector) {
        this.logSelector(selector);
        if (browser.isExisting(selector)) {
            return browser.element(selector);
        } else return null;
    }

}

module.exports = new Util();