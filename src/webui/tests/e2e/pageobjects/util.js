const DEBUG = process.env.DEBUG

var log = console.log

console.log = function() {
    var first_parameter = arguments[0]
    var other_parameters = Array.prototype.slice.call(arguments, 1)

    function formatConsoleDate(date) {
        var hour = date.getHours()
        var minutes = date.getMinutes()
        var seconds = date.getSeconds()
        var milliseconds = date.getMilliseconds()

        return (
            '[' +
            (hour < 10 ? '0' + hour : hour) +
            ':' +
            (minutes < 10 ? '0' + minutes : minutes) +
            ':' +
            (seconds < 10 ? '0' + seconds : seconds) +
            '.' +
            ('00' + milliseconds).slice(-3) +
            '] '
        )
    }

    log.apply(console, [formatConsoleDate(new Date()) + first_parameter].concat(other_parameters))
}

/**
 * Utilities for logging and working with the WebdriverIO API.
 */
class Util {
    logSelector(selector, debug = DEBUG) {
        if (debug) {
            console.log(`Finding element using selector '${selector}'`)
        }
    }

    log(msg, debug = DEBUG) {
        if (debug) {
            console.log(msg)
        }
    }

    elementOrNull(selector) {
        this.logSelector(selector)
        const el = $(selector)
        if (el.isExisting()) {
            return el
        } else {
            return null
        }
    }

    element(selector) {
        const el = $(selector)
        el.waitForDisplayed()
        return el
    }

    elementIntoView(selector) {
        // Get element, scroll into view (middle of screen), and return element
        const el = this.element(selector)
        el.scrollIntoView({ block: 'center', inline: 'center' })
        browser.pause(20) // Scrolling can take a tiny amount of time
        return el
    }

    clearUnexpectedAlerts() {
        // occasionally get alerts for no known reason, here we can dump the text and move on
        // only works for chromium, but that's all we test anyway
        if (browser.isAlertOpen()) {
            console.warn(`Got unexpected alert with text: ${browser.getAlertText()}`)
            browser.dismissAlert()
        }
    }
}

module.exports = new Util()
