/* jshint esnext: true */

workbench.directive('frequencyDetails', function () {
    return {
        restrict: 'E',
        scope: {},
        bindToController: {
            allele: '=',
            group: '@'
        },
        templateUrl: 'ngtmpl/frequencyDetailsWidget.ngtmpl.html',
        controller: FrequencyDetailsWidget,
        controllerAs: 'vm'
    };
});


class FrequencyDetailsWidget {


    constructor(Config) {
        this.config = Config.getConfig();
        this.precision = 4;
    }


}

FrequencyDetailsWidget.$inject = ['Config'];
