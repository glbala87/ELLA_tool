import thenBy from 'thenby'
import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'
import { Compute } from 'cerebral'
import getWarningCleared from '../store/modules/views/workflows/worklog/computed/getWarningCleared'
import getPriority from '../store/modules/views/workflows/worklog/computed/getPriority'
import getReviewComment from '../store/modules/views/workflows/worklog/computed/getReviewComment'
import canClearWarning from '../store/modules/views/workflows/worklog/computed/canClearWarning'
import canCreateInterpretationLog from '../store/modules/views/workflows/worklog/computed/canCreateInterpretationLog'
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
            commentTemplates: state`app.commentTemplates`,
            warningCleared: getWarningCleared,
            reviewComment: getReviewComment,
            canCreateInterpretationLog,
            canClearWarning,
            priority: getPriority,
            priorityOptions: getPriorityOptions,
            showMessagesOnly: state`views.workflows.worklog.showMessagesOnly`,
            messageIds: state`views.workflows.worklog.messageIds`,
            message: state`views.workflows.worklog.message`,
            clearWarningClicked: signal`views.workflows.worklog.clearWarningClicked`,
            priorityChanged: signal`views.workflows.worklog.priorityChanged`,
            addMessageClicked: signal`views.workflows.worklog.addMessageClicked`,
            messageChanged: signal`views.workflows.worklog.messageChanged`,
            updateReviewCommentClicked: signal`views.workflows.worklog.updateReviewCommentClicked`,
            showMessagesOnlyChanged: signal`views.workflows.worklog.showMessagesOnlyChanged`
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
                    },
                    reviewCommentEdited() {
                        return $ctrl.modelReviewComment !== $ctrl.reviewComment
                    },
                    getWorkLogCommentTemplates() {
                        return $ctrl.commentTemplates['workLogMessage']
                    }
                })
            }
        ]
    )
})
