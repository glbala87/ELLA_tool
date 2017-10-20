/* jshint esnext: true */

import {Service, Inject} from '../ng-decorators';

@Service({
    serviceName: 'User'
})
@Inject('$resource')
class UserService {

    constructor(resource) {
        this.resource = resource;
        this.base = '/api/v1';
        this.user = null;
    }

    hasUser() {
        return this.user !== null;
    }

    getCurrentUserId() {
        if (this.hasUser()) {
            return this.user.id;
        }

        return undefined;

    }

    getCurrentUser() {
        if (this.hasUser()) {
            return this.user;
        }
        return this.user;
    }

    loadUser() {
        return new Promise((resolve, reject) => {
            if (this.user !== null) {
                resolve(this.user);
            } else {
                let r = this.resource(`${this.base}/users/currentuser/`);
                let user = r.get(() => {
                    this.setCurrentUser(user);
                    resolve(user);
                }, reject);
            }
        });
    }

    setCurrentUser(user) {
        this.user = user;
        sessionStorage.clear() // Clear session storage when user changes
    }
    
    getAll() {
        return new Promise((resolve, reject) => {
            let r = this.resource(`${this.base}/users/`);
            let users = r.query(() => {
                resolve(users);
            }, reject);
        });
    }

}


export default UserService;
