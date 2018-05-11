import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'
import getClinvarAnnotation from '../../store/common/computes/getClinvarAnnotation'

app.component('alleleInfoClinvar', {
    templateUrl: 'ngtmpl/alleleInfoClinvar.ngtmpl.html',
    controller: connect(
        {
            allele: state`views.workflows.data.alleles.${state`views.workflows.selectedAllele`}`,
            clinvarAnnotation: getClinvarAnnotation(
                state`views.workflows.data.alleles.${state`views.workflows.selectedAllele`}`
            )
        },
        'AlleleInfoClinvar'
    )
})
