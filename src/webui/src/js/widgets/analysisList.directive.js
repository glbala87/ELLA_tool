/* jshint esnext: true */

(function() {

    workbench.directive('analysisList', function () {
        return {
            restrict: 'E',
            scope: {},
            bindToController: {
                analyses: '='
            },
            controller: () => {},
            controllerAs: 'vm',
            templateUrl: 'ngtmpl/analysisList.ngtmpl.html',
        };
    });

}());
