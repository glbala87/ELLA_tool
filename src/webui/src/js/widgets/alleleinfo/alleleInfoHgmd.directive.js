import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'

app.component('alleleInfoHgmd', {
    templateUrl: 'ngtmpl/alleleInfoHgmd.ngtmpl.html',
    controller: connect(
        {
            allele: state`views.workflows.data.alleles.${state`views.workflows.selectedAllele`}`
        },
        'AlleleInfoHgmd'
    )
})
