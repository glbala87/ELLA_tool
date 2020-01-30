/* jshint esnext: true */

import { app } from '../ng-decorators'

app.component('textCounter', {
    bindings: {
        number: '<',
        increment: '<?',
        delay: '<?'
    },
    template: '{{$ctrl.currentCount}}',
    controller: [
        '$interval',
        '$scope',
        function($interval, $scope) {
            const $ctrl = $scope.$ctrl
            $ctrl.currentCount = 0
            $ctrl.increment = $ctrl.increment || 10
            $ctrl.delay = $ctrl.delay || 10
            $interval(
                () => {
                    const currentCount = $ctrl.currentCount + $ctrl.increment
                    $ctrl.currentCount = currentCount >= $ctrl.number ? $ctrl.number : currentCount
                },
                $ctrl.delay,
                $ctrl.number / $ctrl.increment + 1
            )
        }
    ]
})
