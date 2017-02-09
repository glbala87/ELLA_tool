var Page = require('./page')


class LoginPage extends Page {

    open(page) {
        super.open('login');
    }

    get login() { return 'login' }

    _selectUser(number) {
       this.open();
       browser.waitForExist(this.login);
       browser.click(`.list-item.clickable:nth-child(${number})`);
       browser.waitForExist(this.login, 1000, true)
    }

    selectFirstUser() {
        this._selectUser(1);
    }

    selectSecondUser() {
        this._selectUser(2);
    }

    selectThirdUser() {
        this._selectUser(3);
    }

}

module.exports = LoginPage

