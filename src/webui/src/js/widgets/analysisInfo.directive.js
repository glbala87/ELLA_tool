/* jshint esnext: true */

import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'

app.component('analysisInfo', {
    templateUrl: 'ngtmpl/analysisInfo-new.ngtmpl.html',
    controller: connect(
        {
            analysis: state`views.workflows.data.analysis`
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
        let sort = firstBy(a => a.allele.annotation.filtered[0].symbol).thenBy(a => {
            let s = a.allele.annotation.filtered[0].HGVSc_short || a.allele.getHGVSgShort()
            let d = parseInt(s.match(/[cg]\.(\d+)/)[1])
            return d
        })

        let alleles = this.alleles.unclassified.concat(this.alleles.classified)
        return alleles.sort(sort)
    }
}
