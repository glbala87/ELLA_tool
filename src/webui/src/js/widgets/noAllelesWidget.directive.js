/* jshint esnext: true */

(function() {

    workbench.directive('noAllelesWidget', function () {
        return {
            restrict: 'E',
            scope: {
                allele: '='
            },
            templateUrl: 'ngtmpl/noAllelesWidget.ngtmpl.html',
        };
    });

}());
