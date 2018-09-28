import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'

import template from './navbar.ngtmpl.html'
import workflowInterpretationRoundsTemplate from '../widgets/allelebar/interpretationRoundsPopover.ngtmpl.html'

app.component('navbar', {
    transclude: true,
    templateUrl: 'navbar.ngtmpl.html',
    controller: connect(
        {
            config: state`app.config`,
            user: state`app.user`,
            broadcast: state`app.broadcast`,
            currentView: state`views.current`,
            title: state`app.navbar.title`,
            currentView: state`views.current`
        },
        'Navbar'
    )
})
