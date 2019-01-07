import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import template from './modal.ngtmpl.html'

app.component('modal', {
    bindings: {
        name: '@',
        dismissSignal: '=?' // If given, run signal when clicking outside
    },
    templateUrl: 'modal.ngtmpl.html',
    transclude: true,
    controller: connect({}, 'Modal', [
        '$scope',
        'cerebral',
        ($scope, cerebral) => {
            const $ctrl = $scope.$ctrl

            document.body.classList.add('modal-open')
            $scope.$on('$destroy', () => {
                document.body.classList.remove('modal-open')
            })
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
