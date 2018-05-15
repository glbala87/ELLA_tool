import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'
import { Compute } from 'cerebral'
import isReadOnly from '../store/modules/views/workflows/computed/isReadOnly'
import hasAlleles from '../store/modules/views/workflows/computed/hasAlleles'
import getVerificationStatus from '../store/modules/views/workflows/interpretation/computed/getVerificationStatus'
import sortAlleles from '../store/modules/views/workflows/computed/sortAlleles'

app.component('analysisInfo', {
    templateUrl: 'ngtmpl/analysisInfo.ngtmpl.html',
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
