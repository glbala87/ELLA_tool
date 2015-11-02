/* jshint esnext: true */

(function () {
    angular.module('workbench')
        .factory('User', ['$resource', '$cookies', function ($resource, $cookies) {
            return new UserService($resource, $cookies);
        }]);


    class UserService {

        constructor(resource, cookies) {
            this.resource = resource;
            this.cookies = cookies;
            this.currentUserKey = 'currentUsername';
            this.base = '/api/v1';
            this.currentUser = null;
        }

        getCurrentUser() {
            return new Promise((resolve, reject) => {
                if (this.currentUser) {

                    return resolve(this.currentUser);
                }
                else {
                    // Check cookie whether user has selected a user
                    let username = this.cookies.get(this.currentUserKey);
                    if (username) {
                        let r = this.resource(`${this.base}/users/${username}/`);
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
            this.cookies.put(this.currentUserKey, user.username);
        }
    }

})();
