import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'
import template from './alleleInfoHgmd.ngtmpl.html'

app.component('alleleInfoHgmd', {
    template,
    controller: connect(
        {
            allele: state`views.workflows.data.alleles.${state`views.workflows.selectedAllele`}`
        },
        'AlleleInfoHgmd'
    )
})
