import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state } from 'cerebral/tags'
import isReadOnly from '../store/modules/views/workflows/computed/isReadOnly'
import template from './analysisInfo.ngtmpl.html'
import getSamples from '../store/modules/views/workflows/computed/getSamples'
import getWarningCleared from '../store/modules/views/workflows/worklog/computed/getWarningCleared'

app.component('analysisInfo', {
    templateUrl: 'analysisInfo.ngtmpl.html',
    controller: connect(
        {
            warningCleared: getWarningCleared,
            samples: getSamples,
            analysis: state`views.workflows.data.analysis`,
            readOnly: isReadOnly
        },
        'AnalysisInfo',
        [
            '$scope',
            ($scope) => {
                const $ctrl = $scope.$ctrl

                $ctrl.warningOptions = {
                    clearedChecked: false,
                    collapsed: false
                }

                Object.assign($ctrl, {
                    // This is a bit of a hack to copy the computes initial value into controller's
                    // model. We cannot connect the collapse directly to the compute, or it will modify the property
                    // directly on the scope
                    getWarningOptions() {
                        if (!$ctrl.warningOptions.clearedChecked && $ctrl.warningCleared !== null) {
                            $ctrl.warningOptions.collapsed = $ctrl.warningCleared
                            $ctrl.warningOptions.clearedChecked = true
                        }
                        return $ctrl.warningOptions
                    }
                })
            }
        ]
    )
})
