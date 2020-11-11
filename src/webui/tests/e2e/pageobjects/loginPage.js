var Page = require('./page')
var util = require('./util')

const PASSWORD = 'demo'

class LoginPage extends Page {
    open() {
        super.open('login')
    }

    get login() {
        return $('login')
    }

    loginAs(username) {
        // alerts are occasionally thrown here in no reproducible way, try to clear and dump the text to log
        util.clearUnexpectedAlerts()
        this.login.waitForExist()
        $(`.id-username`).setValue(username)
        $(`.id-password`).setValue(PASSWORD)
        $(`.id-login-submit`).click()
        this.login.waitForExist(undefined, true)
    }
}

module.exports = LoginPage
