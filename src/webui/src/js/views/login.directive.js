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
        this.loginForm = {
            "username": "",
            "password": "",
        }

        Navbar.clearItems();
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
        this.loginForm.username = "";
        this.loginForm.password = "";

        this.loginResource.login(username, password).then( () => {
            this.user.loadUser().then(
                this.location.path('/')
             )
             console.log("Successful login")
        }).catch(() => {
            this.toastr.error("Login was unsuccessful")
            console.log("Unsuccessful login")

        })
    }

    resetPassword() {

    }

}
