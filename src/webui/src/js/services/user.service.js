/* jshint esnext: true */

(function() {
    angular.module('workbench')
        .factory('User', ['$resource', function($resource) {
            return new UserService($resource);
    }]);


    class UserService {

        constructor(resource) {
            this.resource = resource;
            this.base = 'http://localhost:5000/api/v1';
            this.currentUser = null;
        }

        getCurrentUser(pmids) {
            return new Promise((resolve, reject) => {
                if (this.currentUser) {
                    return resolve(this.currentUser);
                }

                // TODO: Implement proper way of getting current user, this is dev only
                let r = this.resource(`${this.base}/users/testuser1/`);
                let user = r.get(() => {
                    this.currentUser = user;
                    resolve(user);
                });
            });
        }
    }

})();
