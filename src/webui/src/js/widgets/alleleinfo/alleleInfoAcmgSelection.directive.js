import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'

import isReadOnly from '../../store/modules/views/workflows/computed/isReadOnly'
import getSuggestedAcmgCodes from '../../store/modules/views/workflows/interpretation/computed/getSuggestedAcmgCodes'
import isAlleleAssessmentReused from '../../store/modules/views/workflows/interpretation/computed/isAlleleAssessmentReused'
import getReqCodes from '../../store/modules/views/workflows/interpretation/computed/getReqCodes'
import template from './alleleInfoAcmgSelection.ngtmpl.html'

app.component('alleleInfoAcmgSelection', {
    templateUrl: 'alleleInfoAcmgSelection.ngtmpl.html',
    controller: connect(
        {
            allele: state`views.workflows.data.alleles.${state`views.workflows.selectedAllele`}`,
            readOnly: isReadOnly,
            alleleAssessmentReused: isAlleleAssessmentReused(state`views.workflows.selectedAllele`),
            suggestedAcmgCodes: getSuggestedAcmgCodes(state`views.workflows.selectedAllele`),
            reqCodes: getReqCodes(state`views.workflows.selectedAllele`),
            addAcmgClicked: signal`views.workflows.interpretation.addAcmgClicked`,
            acmgCodeChanged: signal`views.workflows.interpretation.acmgCodeChanged`
        },
        'AlleleInfoACMGSelection',
        [
            '$scope',
            ($scope) => {
                const $ctrl = $scope.$ctrl

                Object.assign($ctrl, {
                    acmgCodeChangedWrapper(code) {
                        $ctrl.acmgCodeChanged({
                            alleleId: $ctrl.allele.id,
                            code: code
                        })
                    },
                    addAcmgFromReq(code) {
                        $ctrl.addAcmgClicked({
                            alleleId: $ctrl.allele.id,
                            code: {
                                code: code,
                                source: 'user'
                            }
                        })
                    },
                    isEditable() {
                        return !$ctrl.readOnly && !$ctrl.alleleAssessmentReused
                    },
                    isUpgradeOrDowngradable() {
                        return false // Suggested or reqs shouldn't be up/downgradable
                    }
                })
            }
        ]
    )
})
