/* jshint esnext: true */

import {Directive, Inject} from '../ng-decorators';

@Directive({
    selector: 'login',
    templateUrl: 'ngtmpl/login.ngtmpl.html'
})
@Inject('$location', 'User')
export class LoginController {
    constructor(location, User) {
        this.location = location;
        this.user = User;
        this.users = [];
        this.name_filter = '';
        this.loadUsers();
    }

    loadUsers() {
        this.user.getUsers().then(users => {
            this.users = users;
        });
    }

    selectUser(user) {
        this.user.setCurrentUser(user);
        this.location.path('/');
    }
}
