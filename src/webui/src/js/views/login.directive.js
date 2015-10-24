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
        constructor(router, interpretationService) {
            this.router = router;

        }

    }

    LoginVM.$inject = ['$route'];

})();
