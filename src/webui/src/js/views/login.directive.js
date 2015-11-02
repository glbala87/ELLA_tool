/* jshint esnext: true */


(function () {
    workbench.directive('login', function () {
        return {
            restrict: 'E',
            templateUrl: 'ngtmpl/login.ngtmpl.html',
            controller: LoginVM,
            controllerAs: 'vm'
        };
    });


    class LoginVM {
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

    LoginVM.$inject = ['$location', 'User'];

})();
