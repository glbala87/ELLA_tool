var Page = require('./page')

var users = [['testuser1', 'demo'], ['testuser2', 'demo'], ['testuser3', 'demo']]

class LoginPage extends Page {
    open() {
        super.open('login')
    }

    get login() {
        return 'login'
    }

    _selectUser(number) {
        const login = $(this.login)
        login.waitForExist()
        $(`.id-username`).setValue(users[number][0])
        $(`.id-password`).setValue(users[number][1])
        $(`.id-login-submit`).click()
        login.waitForExist(undefined, true)
    }

    selectFirstUser() {
        this._selectUser(0)
    }

    selectSecondUser() {
        this._selectUser(1)
    }

    selectThirdUser() {
        this._selectUser(2)
    }
}

module.exports = LoginPage
