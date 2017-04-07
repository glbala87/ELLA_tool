/* jshint esnext: true */

import {Directive, Inject} from '../ng-decorators';

@Directive({
    selector: 'login',
    templateUrl: 'ngtmpl/login.ngtmpl.html'
})
@Inject('$location', 'User', 'Navbar', 'LoginResource', 'toastr')
export class LoginController {
    constructor(location, User,Navbar, LoginResource, toastr) {
        this.location = location;
        this.user = User;
        this.users = [];
        this.toastr = toastr;
        this.name_filter = '';
        this.loginResource = LoginResource;
        this.resetPasswordFlag = false;
        this.reset()
        Navbar.clearItems();
    }

    reset() {
        this.loginForm = {
            "username": "",
            "password": "",
            "new_password": "",
            "confirm_password": "",
        }
    }

    selectUser(user) {
        this.user.setCurrentUser(user);
        this.location.path('/');
    }

    login() {
        // Reset current user
        this.user.setCurrentUser(null);

        let username = this.loginForm.username;
        let password = this.loginForm.password;
        this.reset()

        this.loginResource.login(username, password).then( () => {
            this.user.loadUser().then(
                this.location.path('/')
             )
             console.log("Successful login")
        }).catch((error) => {
            this.toastr.error(`Login was unsuccessful: ${error}`)
            console.log("Unsuccessful login")
            console.log(error)

        })
    }

    resetPassword() {
        if (!this.resetPasswordFlag) {
            this.resetPasswordFlag = true;
            return
        }

        let username = this.loginForm.username;
        let password = this.loginForm.password;
        let new_password = this.loginForm.new_password;
        this.reset()

        this.loginResource.resetPassword(username, password, new_password).then( () => {
            console.log("Reloading...")
            window.location.reload()
             console.log("Successful password reset")
        }).catch((error) => {
            this.toastr.error(`Change password was unsuccessful: ${error}`)
            console.log(error)

        })

    }

    changePasswordOk() {
        if (!this.resetPasswordFlag) {
            return false
        }

        return this.loginForm.new_password === this.loginForm.confirm_password

    }


}
