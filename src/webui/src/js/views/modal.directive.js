import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, props, signal } from 'cerebral/tags'

app.component('modal', {
    bindings: {
        name: '@',
        dismissSignal: '=?' // If given, run signal when clicking outside
    },
    templateUrl: 'ngtmpl/modal.ngtmpl.html',
    transclude: true,
    controller: connect({}, 'Modal', [
        '$scope',
        'cerebral',
        ($scope, cerebral) => {
            const $ctrl = $scope.$ctrl

            Object.assign($ctrl, {
                dismiss() {
                    if ($ctrl.dismissSignal) {
                        cerebral.controller.getSignal($ctrl.dismissSignal)({
                            modalName: $ctrl.name
                        })
                    }
                }
            })
        }
    ])
})