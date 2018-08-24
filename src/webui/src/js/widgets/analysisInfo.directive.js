import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'
import isReadOnly from '../store/modules/views/workflows/computed/isReadOnly'
import template from './analysisInfo.ngtmpl.html'
import getSamples from '../store/modules/views/workflows/computed/getSamples'

app.component('analysisInfo', {
    templateUrl: 'analysisInfo.ngtmpl.html',
    controller: connect(
        {
            samples: getSamples,
            analysis: state`views.workflows.data.analysis`,
            readOnly: isReadOnly
        },
        'AnalysisInfo'
    )
})
