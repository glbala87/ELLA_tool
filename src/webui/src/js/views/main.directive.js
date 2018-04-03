import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'

app.component('main', {
    templateUrl: 'ngtmpl/main.ngtmpl.html',
    controller: connect(
        {
            views: state`views`,
            modals: state`modals`
        },
        'Main'
    )
})
