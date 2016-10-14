var Page = require('./page')


class LoginPage extends Page {

    get login() { return 'login' }

    _selectUser(number) {
       this.open()
       browser.waitForExist(this.login)
       browser.click(`.list-item.clickable:nth-child(${number})`)
       browser.waitForExist(this.login, 1000, true)
    }

    open(page) {
        super.open('login');
    }

    selectFirstUser() {
        this._selectUser(1);
    }
}

module.exports = LoginPage

