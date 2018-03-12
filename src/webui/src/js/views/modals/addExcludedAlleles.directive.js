import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'

app.component('addExcludedAlleles', {
    templateUrl: 'ngtmpl/addExcludedAlleles.ngtmpl.html',
    controller: connect(
        {
            config: state`app.config`,
            alleles: state`views.workflows.modals.addExcludedAlleles.data.alleles`
        },
        'AddExcludedAlleles'
    )
})
