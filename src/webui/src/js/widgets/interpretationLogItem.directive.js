import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, props, signal } from 'cerebral/tags'
import template from './interpretationLogItem.ngtmpl.html' // eslint-disable-line no-unused-vars

app.component('interpretationLogItem', {
    templateUrl: 'interpretationLogItem.ngtmpl.html',
    bindings: {
        messageId: '<'
    },
    controller: connect(
        {
            config: state`app.config`,
            message: state`views.workflows.worklog.messages.${props`messageId`}`,
            editMessageClicked: signal`views.workflows.worklog.editMessageClicked`,
            deleteMessageClicked: signal`views.workflows.worklog.deleteMessageClicked`
        },
        'InterpretationLogItem',
        [
            '$scope',
            function($scope) {
                const $ctrl = $scope.$ctrl

                $ctrl.mode = 'normal'

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
                    },
                    getMessageModel() {
                        if ($ctrl.mode === 'edit') {
                            return $ctrl.editedMessage
                        }
                        return $ctrl.message
                    },
                    editClicked() {
                        $ctrl.mode = 'edit'
                        $ctrl.editedMessage = Object.assign({}, $ctrl.message)
                    },
                    editConfirmed() {
                        $ctrl.editMessageClicked({
                            interpretationLog: {
                                id: $ctrl.message.originalId,
                                message: $ctrl.editedMessage.message
                            }
                        })
                        $ctrl.mode = 'normal'
                    },
                    editAborted() {
                        $ctrl.mode = 'normal'
                        $ctrl.editedMessage = null
                    },
                    deleteClicked() {
                        $ctrl.mode = 'delete'
                    },
                    deleteConfirmed() {
                        $ctrl.deleteMessageClicked({ id: $ctrl.message.originalId })
                        $ctrl.mode = 'normal'
                    },
                    deleteAborted() {
                        $ctrl.mode = 'normal'
                    },
                    getClasses() {
                        const classes = []
                        if ($ctrl.message.editable) {
                            classes.push('editable')
                        }
                        if ($ctrl.message.message) {
                            classes.push('has-message')
                        }
                        if ($ctrl.mode === 'normal') {
                            classes.push('normal-mode')
                        }
                        if ($ctrl.mode === 'edit') {
                            classes.push('edit-mode')
                        }
                        if ($ctrl.mode === 'delete') {
                            classes.push('delete-mode')
                        }
                        return classes
                    },
                    getAlleleAssessmentMessage() {
                        const reportText = $ctrl.message.allelereport && $ctrl.message.allelereport.allele_id
                            ? ' and variant report'
                            : ''
                        return `Updated classification${reportText} for `
                    },
                    getAlleleAssessmentClassification() {
                        const classToText = (cl) => {
                            const optionClass = $ctrl.config.classification.options.find(
                                (o) => o.value === cl
                            )
                            return optionClass ? optionClass.name : cl
                        }
                        const fromText = $ctrl.message.alleleassessment.previous_classification
                            ? `${classToText(
                                  $ctrl.message.alleleassessment.previous_classification
                              )} `
                            : ''
                        return `(${fromText}→ ${classToText(
                            $ctrl.message.alleleassessment.classification
                        )})`
                    },
                    getAlleleReportMessage() {
                        return `Updated variant report for `
                    }
                })
            }
        ]
    )
})
