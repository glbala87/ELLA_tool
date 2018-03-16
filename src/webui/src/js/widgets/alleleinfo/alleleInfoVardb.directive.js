/* jshint esnext: true */

import { Directive, Inject } from '../../ng-decorators'
import { AlleleStateHelper } from '../../model/allelestatehelper'

import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'

import isReadOnly from '../../store/modules/views/workflows/computed/isReadOnly'

app.component('alleleInfoClassification', {
    templateUrl: 'ngtmpl/alleleInfoClassification.ngtmpl.html',
    controller: connect(
        {
            allele: state`views.workflows.data.alleles.${state`views.workflows.selectedAllele`}`,
            readOnly: isReadOnly,
            showAlleleAssessmentHistory: signal`views.workflows.interpretation.showAlleleAssessmentHistoryClicked`
        },
        'AlleleInfoClassification'
    )
})

@Directive({
    selector: 'allele-info-vardb',
    scope: {
        allele: '=',
        alleleState: '=',
        readOnly: '=?'
    },
    templateUrl: 'ngtmpl/alleleInfoVardb.ngtmpl.html'
})
@Inject('Config', 'AlleleAssessmentHistoryModal')
export class AlleleInfoVardb {
    constructor(Config, AlleleAssessmentHistoryModal) {
        this.config = Config.getConfig()
        this.alleleAssessmentHistoryModal = AlleleAssessmentHistoryModal
    }

    hasContent() {
        return Boolean(this.allele.allele_assessment)
    }

    showHistory() {
        this.alleleAssessmentHistoryModal.show(this.allele.id)
    }
}
