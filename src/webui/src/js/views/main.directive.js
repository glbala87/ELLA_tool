import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'

import template from './main.ngtmpl.html'

app.component('main', {
    templateUrl: 'main.ngtmpl.html',
    controller: connect(
        {
            views: state`views`,
            modals: state`modals`
        },
        'Main'
    )
})
