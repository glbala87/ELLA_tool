/* jshint esnext: true */

import { app } from '../ng-decorators'
import template from './confirmButton.ngtmpl.html' // eslint-disable-line no-unused-vars

app.component('confirmButton', {
    bindings: {
        ngDisabled: '<?',
        color: '@?',
        confirmAction: '<', // Function to call upon confirm
        confirmColor: '@?'
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
                },
                getConfirmClasses() {
                    const classes = []
                    if (!$ctrl.needsConfirmation || $ctrl.ngDisabled) {
                        classes.push('hidden')
                    }
                    if ($ctrl.confirmColor) {
                        classes.push(`confirm-${$ctrl.confirmColor}`)
                    } else {
                        classes.push('confirm-green')
                    }
                    return classes
                }
            })
        }
    ]
})
