import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, props, signal } from 'cerebral/tags'
import getReferenceAssessment from '../../store/modules/views/workflows/interpretation/computed/getReferenceAssessment'
import isReadOnly from '../../store/modules/views/workflows/computed/isReadOnly'
import isAlleleAssessmentReused from '../../store/modules/views/workflows/interpretation/computed/isAlleleAssessmentReused'
import template from './alleleInfoReferenceDetail.ngtmpl.html'

app.component('alleleInfoReferenceDetail', {
    bindings: {
        referenceId: '='
    },
    template,
    controller: connect(
        {
            selectedAllele: state`views.workflows.selectedAllele`,
            reference: state`views.workflows.data.references.${props`referenceId`}`,
            readOnly: isReadOnly,
            alleleAssessmentReused: isAlleleAssessmentReused(state`views.workflows.selectedAllele`),
            referenceAssessment: getReferenceAssessment(
                state`views.workflows.selectedAllele`,
                props`referenceId`
            ),
            ignoreReferenceClicked: signal`views.workflows.interpretation.ignoreReferenceClicked`,
            evaluateReferenceClicked: signal`views.workflows.interpretation.evaluateReferenceClicked`
        },
        'AlleleInfoReferenceDetail',
        [
            '$scope',
            function($scope) {
                const $ctrl = $scope.$ctrl

                Object.assign($ctrl, {
                    getEvaluateBtnText() {
                        if ($ctrl.readOnly || $ctrl.alleleAssessmentReused) {
                            return 'See details'
                        }
                        if ($ctrl.referenceAssessment) {
                            return 'Re-evaluate'
                        }
                        return 'Evaluate'
                    }
                })
            }
        ]
    )
})
