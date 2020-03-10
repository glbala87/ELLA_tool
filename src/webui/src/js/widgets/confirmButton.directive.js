/* jshint esnext: true */

import { app } from '../ng-decorators'
import template from './confirmButton.ngtmpl.html'

app.component('confirmButton', {
    bindings: {
        ngDisabled: '<?',
        color: '@?',
        confirmAction: '<' // Function to call upon confirm
    },
    transclude: true,
    templateUrl: 'confirmButton.ngtmpl.html',
    controller: [
        '$scope',
        function($scope) {
            const $ctrl = $scope.$ctrl

            Object.assign($ctrl, {
                needsConfirmation: false,
                toggleConfirm() {
                    $ctrl.needsConfirmation = !$ctrl.needsConfirmation
                },
                confirm() {
                    $ctrl.confirmAction()
                    $ctrl.needsConfirmation = false
                },
                getClasses() {
                    const classes = []
                    if ($ctrl.needsConfirmation) {
                        classes.push('active')
                    }
                    if ($ctrl.color) {
                        classes.push($ctrl.color)
                    }
                    return classes
                }
            })
        }
    ]
})
