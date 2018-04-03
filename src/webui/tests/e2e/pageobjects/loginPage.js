var Page = require('./page')

var users = [['testuser1', 'demo'], ['testuser2', 'demo'], ['testuser3', 'demo']]

class LoginPage extends Page {
    open(page) {
        super.open('login')
    }

    get login() {
        return 'login'
    }

    _selectUser(number) {
        this.open()
        browser.waitForExist(this.login)
        browser.setValue(`.id-username`, users[number][0])
        browser.setValue(`.id-password`, users[number][1])
        browser.click(`.id-login-submit`)
        browser.waitForExist(this.login, 1000, true)
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
