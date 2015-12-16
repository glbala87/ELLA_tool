/* jshint esnext: true */

import {Service, Inject} from '../ng-decorators';

@Service({
    serviceName: 'User'
})
@Inject('$resource', '$cookies')
class UserService {

    constructor(resource, cookies) {
        this.resource = resource;
        this.cookies = cookies;
        this.currentUserKey = 'currentUserId';
        this.base = '/api/v1';
        this.currentUser = null;
    }

    getCurrentUserId() {
        return parseInt(this.cookies.get(this.currentUserKey), 10);
    }

    getCurrentUser() {
        return new Promise((resolve, reject) => {
            if (this.currentUser) {

                return resolve(this.currentUser);
            }
            else {
                // Check cookie whether user has selected a user
                let user_id = this.getCurrentUserId();
                if (user_id) {
                    let r = this.resource(`${this.base}/users/${user_id}/`);
                    let user = r.get(() => {
                        this.currentUser = user;
                        resolve(user);
                    });
                }
                else {
                    return resolve(null);
                }
            }
        });
    }

    getUsers() {
        return new Promise((resolve, reject) => {
            let r = this.resource(`${this.base}/users/`);
            let users = r.query(() => {
                resolve(users);
            });
        });
    }

    setCurrentUser(user) {
        this.currentUser = user;
        this.cookies.put(this.currentUserKey, user.id);
    }
}


export default UserService;
