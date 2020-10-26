/* jshint esnext: true */

import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { signal, state } from 'cerebral/tags'
import template from './alleleAssessmentHistory.ngtmpl.html'

app.component('alleleAssessmentHistory', {
    templateUrl: 'alleleAssessmentHistory.ngtmpl.html',
    controller: connect(
        {
            alleleAssessments: state`views.workflows.modals.alleleAssessmentHistory.data.alleleassessments`,
            selectedAlleleAssessment: state`views.workflows.modals.alleleAssessmentHistory.selectedAlleleAssessment`,
            //attachments: state`views.workflows.modals.alleleAssessmentHistory.data.attachments`,
            selectedAlleleAssessmentChanged: signal`views.workflows.modals.alleleAssessmentHistory.selectedAlleleAssessmentChanged`,
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
