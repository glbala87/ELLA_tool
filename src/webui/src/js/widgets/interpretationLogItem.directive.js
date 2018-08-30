import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, props, signal } from 'cerebral/tags'
import { compute } from 'cerebral'
import template from './interpretationLogItem.ngtmpl.html'

app.component('interpretationLogItem', {
    templateUrl: 'interpretationLogItem.ngtmpl.html',
    bindings: {
        logId: '<'
    },
    controller: connect(
        {
            config: state`app.config`,
            log: state`views.workflows.data.interpretationlogs.${props`logId`}`
        },
        'InterpretationLogItem',
        [
            '$scope',
            function($scope) {
                const $ctrl = $scope.$ctrl
                Object.assign($ctrl, {
                    formatPriority() {
                        if (!$ctrl.log.priority) {
                            return 'N/A'
                        }
                        return $ctrl.config.analysis.priority.display[$ctrl.log.priority]
                    },
                    formatUser() {
                        if (!$ctrl.log.user) {
                            return 'System'
                        }
                        return $ctrl.log.user.full_name
                    }
                })
            }
        ]
    )
})
