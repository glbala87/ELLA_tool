import app from '../ng-decorators'
import { state } from 'cerebral/tags'
import { connect } from '@cerebral/angularjs'
import getWarnings from '../store/modules/views/workflows/interpretation/computed/getWarnings'

import template from './alleleWarning.ngtmpl.html'

app.component('alleleWarning', {
    templateUrl: 'alleleWarning.ngtmpl.html',
    controller: connect(
        {
            warnings: getWarnings(
                state`views.workflows.interpretation.data.alleles.${state`views.workflows.selectedAllele`}`
            )
        },
        'AlleleWarning'
    )
})
