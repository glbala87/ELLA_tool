const DEBUG = process.env.DEBUG;

var log = console.log;

console.log = function () {
    var first_parameter = arguments[0];
    var other_parameters = Array.prototype.slice.call(arguments, 1);

    function formatConsoleDate (date) {
        var hour = date.getHours();
        var minutes = date.getMinutes();
        var seconds = date.getSeconds();
        var milliseconds = date.getMilliseconds();

        return '[' +
               ((hour < 10) ? '0' + hour: hour) +
               ':' +
               ((minutes < 10) ? '0' + minutes: minutes) +
               ':' +
               ((seconds < 10) ? '0' + seconds: seconds) +
               '.' +
               ('00' + milliseconds).slice(-3) +
               '] ';
    }

    log.apply(console, [formatConsoleDate(new Date()) + first_parameter].concat(other_parameters));
};

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

    elementIntoView(selector) {
        // Get element, scroll into view (middle of screen), and return element
        var el = browser.element(selector)
        browser.scroll(el.selector, 0, -browser.windowHandleSize().value.height/2)
        return el;
    }

}

module.exports = new Util();