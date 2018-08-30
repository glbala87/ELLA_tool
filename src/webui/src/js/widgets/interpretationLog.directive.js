import thenBy from 'thenby'
import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, props, signal } from 'cerebral/tags'
import { Compute } from 'cerebral'
import getInterpretationLogIds from '../store/modules/views/workflows/worklog/computed/getInterpretationLogIds'
import getWarningCleared from '../store/modules/views/workflows/worklog/computed/getWarningCleared'
import getPriority from '../store/modules/views/workflows/worklog/computed/getPriority'
import template from './interpretationLog.ngtmpl.html'

const getPriorityOptions = Compute(state`app.config`, (config) => {
    const options = Object.entries(config.analysis.priority.display)
        .map((i) => [parseInt(i[0]), i[1]])
        .sort(thenBy((i) => i[0]))
    return options
})

app.component('interpretationLog', {
    templateUrl: 'interpretationLog.ngtmpl.html',
    controller: connect(
        {
            config: state`app.config`,
            interpretationLogIds: getInterpretationLogIds,
            warningCleared: getWarningCleared,
            priority: getPriority,
            priorityOptions: getPriorityOptions,
            message: state`views.workflows.worklog.message`,
            clearWarningClicked: signal`views.workflows.worklog.clearWarningClicked`,
            priorityChanged: signal`views.workflows.worklog.priorityChanged`,
            addMessageClicked: signal`views.workflows.worklog.addMessageClicked`,
            messageChanged: signal`views.workflows.worklog.messageChanged`
        },
        'InterpretationLog',
        [
            '$scope',
            function($scope) {
                const $ctrl = $scope.$ctrl
                Object.assign($ctrl, {
                    getClearWarningText() {
                        if ($ctrl.warningCleared) {
                            return 'Reinstate warning'
                        }
                        return 'Clear warning'
                    }
                })
            }
        ]
    )
})
