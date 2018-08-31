import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, props, signal } from 'cerebral/tags'
import { compute } from 'cerebral'
import template from './interpretationLogItem.ngtmpl.html'

app.component('interpretationLogItem', {
    templateUrl: 'interpretationLogItem.ngtmpl.html',
    bindings: {
        messageId: '<'
    },
    controller: connect(
        {
            config: state`app.config`,
            message: state`views.workflows.worklog.messages.${props`messageId`}`
        },
        'InterpretationLogItem',
        [
            '$scope',
            function($scope) {
                const $ctrl = $scope.$ctrl
                Object.assign($ctrl, {
                    formatPriority() {
                        if (!$ctrl.message.priority) {
                            return 'N/A'
                        }
                        return $ctrl.config.analysis.priority.display[$ctrl.message.priority]
                    },
                    formatUser() {
                        if (!$ctrl.message.user) {
                            return 'System'
                        }
                        return $ctrl.message.user.full_name
                    },
                    fromToday() {
                        return (
                            new Date($ctrl.message.date_created).toDateString() ===
                            new Date().toDateString()
                        )
                    }
                })
            }
        ]
    )
})
