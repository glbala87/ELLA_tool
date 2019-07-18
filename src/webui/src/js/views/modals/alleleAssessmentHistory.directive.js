import thenBy from 'thenby'
import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'
import { Compute } from 'cerebral'
import template from './alleleAssessmentHistory.ngtmpl.html'

app.component('alleleAssessmentHistory', {
    templateUrl: 'alleleAssessmentHistory.ngtmpl.html',
    controller: connect(
        {
            alleleAssessments: state`views.workflows.modals.alleleAssessmentHistory.data.alleleAssessments`,
            classificationDetails: state`views.workflows.modals.alleleAssessmentHistory.classificationDetails`,
            selectedAlleleAssessment: state`views.workflows.modals.alleleAssessmentHistory.selectedAlleleAssessment`,
            selectedViewMode: state`views.workflows.modals.alleleAssessmentHistory.selectedViewMode`,
            selectedAlleleAssessmentChanged: signal`views.workflows.modals.alleleAssessmentHistory.selectedAlleleAssessmentChanged`,
            selectedViewModeChanged: signal`views.workflows.modals.alleleAssessmentHistory.selectedViewModeChanged`,
            dismissClicked: signal`views.workflows.modals.alleleAssessmentHistory.dismissClicked`
        },
        'AlleleAssessmentHistory',
        [
            '$scope',
            ($scope) => {
                const $ctrl = $scope.$ctrl

                Object.assign($ctrl, {
                    close() {
                        $ctrl.dismissClicked()
                    },
                    formatAlleleAssessment(aa) {
                        return `${$ctrl.formatDate(aa)}: Class ${aa.classification} by ${
                            aa.user.abbrev_name
                        } on ${aa.genepanel_name}_${aa.genepanel_version}`
                    },
                    formatDate(aa) {
                        return new Date(aa.date_created).toISOString().split('T')[0]
                    }
                })
            }
        ]
    )
})
