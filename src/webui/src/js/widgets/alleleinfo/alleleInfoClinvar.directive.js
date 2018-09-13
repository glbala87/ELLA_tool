import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, props } from 'cerebral/tags'
import getClinvarAnnotation from '../../store/common/computes/getClinvarAnnotation'
import template from './alleleInfoClinvar.ngtmpl.html'

app.component('alleleInfoClinvar', {
    templateUrl: 'alleleInfoClinvar.ngtmpl.html',
    bindings: {
        allelePath: '<'
    },
    controller: connect(
        {
            allele: state`${props`allelePath`}`,
            clinvarAnnotation: getClinvarAnnotation(state`${props`allelePath`}`)
        },
        'AlleleInfoClinvar'
    )
})
