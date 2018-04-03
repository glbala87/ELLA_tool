import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'

import isReadOnly from '../../store/modules/views/workflows/computed/isReadOnly'
import getSuggestedAcmgCodes from '../../store/modules/views/workflows/interpretation/computed/getSuggestedAcmgCodes'
import getReqCodes from '../../store/modules/views/workflows/interpretation/computed/getReqCodes'

app.component('alleleInfoAcmgSelection', {
    templateUrl: 'ngtmpl/alleleInfoAcmgSelection.ngtmpl.html',
    controller: connect(
        {
            allele: state`views.workflows.data.alleles.${state`views.workflows.selectedAllele`}`,
            readOnly: isReadOnly,
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
                    acmgCodeChangedWrapper: (code) => {
                        $ctrl.acmgCodeChanged({
                            alleleId: $ctrl.allele.id,
                            code: code
                        })
                    }
                })
            }
        ]
    )
})
