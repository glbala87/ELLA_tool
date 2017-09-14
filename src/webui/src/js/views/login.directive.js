/* jshint esnext: true */

import {Directive, Inject} from '../ng-decorators';

@Directive({
    selector: 'login',
    templateUrl: 'ngtmpl/login.ngtmpl.html'
})
@Inject('$scope', '$location', 'Config', 'User', 'Navbar', 'LoginResource', 'toastr')
export class LoginController {
    constructor($scope, location, Config, User,Navbar, LoginResource, toastr) {
        this.location = location;
        this.user = User;
        this.users = [];
        this.toastr = toastr;
        this.config = Config.getConfig()
        this.configService = Config;

        this.modes = ["Login", "Change password"];
        this.mode = this.modes[0];

        this.loginForm = {
            "username": "",
            "password": "",
            "new_password": "",
            "confirm_password": "",
        }

        this.loginResource = LoginResource;
        this.reset()
        Navbar.clearItems();

        $scope.$watch(
            () => this.loginForm.new_password,
            () => {this.checkPasswordStrength()}
        )

    }

    checkPasswordStrength() {
        let pw = this.loginForm.new_password;
        let group_matches = 0
        let groups = this.config.user.auth["password_match_groups"]
        let num_match_groups = this.config.user.auth["password_num_match_groups"]
        let min_length = this.config.user.auth["password_minimum_length"]
        this.passWordChecks[0][1] = pw.length >= min_length;

        for (let i in groups) {
            let g = groups[i];
            let r = new RegExp(g)
            let test = r.test(pw);
            this.passWordChecks[parseInt(i)+1][1] = test;
            group_matches += test;
        }

        return group_matches >= num_match_groups && pw.length >= min_length;
    }

    checkPasswordsEqual() {
        return this.loginForm.new_password === this.loginForm.confirm_password;
    }

    checkValidUsername() {
        return this.loginForm.username.length > 0 && !this.loginForm.username.contains(" ");
    }

    reset() {
        this.loginForm.password = "";
        this.loginForm.new_password = "";
        this.loginForm.confirm_password = "";

        // Create list of password requirements
        let minLength = this.config.user.auth["password_minimum_length"]
        this.passWordChecks = [[`Minimum ${minLength} letters`, false]]
        for (let s of this.config.user.auth["password_match_groups_descr"]) {
            this.passWordChecks.push([s, false])
        }
    }

    selectUser(user) {
        this.user.setCurrentUser(user);
        this.location.path('/');
    }

    submit() {
        if (this.mode === this.modes[0]) {
            this.login()
        } else {
            this.resetPassword()
        }
    }


    login() {
        let error = false;
        if (!this.checkValidUsername()) {
            this.toastr.error("Invalid username")
            error = true;
        }

        if (error) {
            return;
        }

        // Reset current user
        this.user.setCurrentUser(null);

        let username = this.loginForm.username;
        let password = this.loginForm.password;
        this.reset()

        this.loginResource.login(username, password).then( () => {
            this.user.loadUser().then(
                this.configService.loadConfig().then( () => {
                        this.location.path('/');
                    }
                )
             )
             console.log("Successful login")
        }).catch((error) => {
            this.toastr.error(`Login was unsuccessful: ${error}`)
            console.log("Unsuccessful login")
            console.log(error)

        })
    }

    resetPassword() {
        let error = false;

        if (!this.checkValidUsername()) {
            this.toastr.error("Invalid username")
            error = true;
        }

        if (!this.checkPasswordStrength()) {
            this.toastr.error("Password not strong enough.")
            error = true;
        }

        if (!this.checkPasswordsEqual()) {
            this.toastr.error("Passwords do not match.")
            error = true;
        }

        if (error) {
            return;
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
}
