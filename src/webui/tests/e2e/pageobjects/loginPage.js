var Page = require('./page')

const PASSWORD = 'demo'

class LoginPage extends Page {
    open() {
        super.open('login')
    }

    get login() {
        return 'login'
    }

    loginAs(username) {
        const login = $(this.login)
        login.waitForExist()
        $(`.id-username`).setValue(username)
        $(`.id-password`).setValue(PASSWORD)
        $(`.id-login-submit`).click()
        login.waitForExist(undefined, true)
    }
}

module.exports = LoginPage
