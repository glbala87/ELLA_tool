/* jshint esnext: true */

import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'
import { Compute } from 'cerebral'
import isReadOnly from '../store/modules/views/workflows/computed/isReadOnly'
import hasAlleles from '../store/modules/views/workflows/computed/hasAlleles'
import getVerificationStatus from '../store/modules/views/workflows/interpretation/computed/getVerificationStatus'
import sortAlleles from '../store/modules/views/workflows/computed/sortAlleles'

app.component('analysisInfo', {
    templateUrl: 'ngtmpl/analysisInfo-new.ngtmpl.html',
    controller: connect(
        {
            analysis: state`views.workflows.data.analysis`,
            alleles: sortAlleles(state`views.workflows.data.alleles`),
            hasAlleles,
            readOnly: isReadOnly,
            verificationStatus: getVerificationStatus,
            verificationStatusChanged: signal`views.workflows.verificationStatusChanged`
        },
        'AnalysisInfo'
    )
})

import { Directive, Inject } from '../ng-decorators'
import { AlleleStateHelper } from '../model/allelestatehelper'

@Directive({
    selector: 'analysis-info-old',
    templateUrl: 'ngtmpl/analysisInfo.ngtmpl.html',
    scope: {
        analysis: '=',
        alleles: '=',
        readOnly: '=?',
        verificationStatusChanged: '&?'
    }
})
@Inject()
export class AnalysisInfoController {
    constructor() {}

    getAlleles() {
        let sort = firstBy((a) => a.allele.annotation.filtered[0].symbol).thenBy((a) => {
            let s = a.allele.annotation.filtered[0].HGVSc_short || a.allele.getHGVSgShort()
            let d = parseInt(s.match(/[cg]\.(\d+)/)[1])
            return d
        })

        let alleles = this.alleles.unclassified.concat(this.alleles.classified)
        return alleles.sort(sort)
    }
}
