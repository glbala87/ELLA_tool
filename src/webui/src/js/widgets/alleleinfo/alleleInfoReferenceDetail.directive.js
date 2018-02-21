import { Directive, Inject } from '../../ng-decorators'

import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, props, signal } from 'cerebral/tags'
import getReferenceAssessment from '../../store/modules/views/workflows/interpretation/computed/getReferenceAssessment'
import isReadOnly from '../../store/modules/views/workflows/computed/isReadOnly'

app.component('alleleInfoReferenceDetail', {
    bindings: {
        referenceId: '='
    },
    templateUrl: 'ngtmpl/alleleInfoReferenceDetail-new.ngtmpl.html',
    controller: connect(
        {
            selectedAllele: state`views.workflows.selectedAllele`,
            reference: state`views.workflows.data.references.${props`referenceId`}`,
            readOnly: isReadOnly,
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
                        if ($ctrl.readOnly) {
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

@Directive({
    selector: 'allele-info-reference-detail-old',
    templateUrl: 'ngtmpl/alleleInfoReferenceDetail.ngtmpl.html',
    scope: {
        reference: '=',
        vm: '='
    },
    replace: true
})
@Inject('$scope')
export class AlleleInfoReferenceDetail {}
