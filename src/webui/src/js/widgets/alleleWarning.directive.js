import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { Compute } from 'cerebral'
import { state } from 'cerebral/tags'
import template from './alleleWarning.ngtmpl.html'

const warnings = Compute(
    state`views.workflows.data.alleles.${state`views.workflows.selectedAllele`}`,
    (allele) => {
        const warnings = []
        if (allele && allele.warnings) {
            for (const [key, warning] of Object.entries(allele.warnings)) {
                warnings.push({ warning })
            }
        }
        return warnings
    }
)

app.component('alleleWarning', {
    templateUrl: 'alleleWarning.ngtmpl.html',
    controller: connect(
        {
            warnings
        },
        'AlleleWarning'
    )
})
