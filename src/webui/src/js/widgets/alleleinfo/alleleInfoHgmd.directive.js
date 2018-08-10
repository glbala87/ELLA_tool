import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'
import template from './alleleInfoHgmd.ngtmpl.html'

app.component('alleleInfoHgmd', {
    templateUrl: 'alleleInfoHgmd.ngtmpl.html',
    controller: connect(
        {
            allele: state`views.workflows.data.alleles.${state`views.workflows.selectedAllele`}`
        },
        'AlleleInfoHgmd'
    )
})
