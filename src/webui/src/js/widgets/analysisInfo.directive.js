import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'
import isReadOnly from '../store/modules/views/workflows/computed/isReadOnly'
import hasAlleles from '../store/modules/views/workflows/computed/hasAlleles'
import sortAlleles from '../store/modules/views/workflows/computed/sortAlleles'
import template from './analysisInfo.ngtmpl.html'

app.component('analysisInfo', {
    templateUrl: 'analysisInfo.ngtmpl.html',
    controller: connect(
        {
            analysis: state`views.workflows.data.analysis`,
            alleles: sortAlleles(state`views.workflows.data.alleles`),
            hasAlleles,
            readOnly: isReadOnly
        },
        'AnalysisInfo'
    )
})
