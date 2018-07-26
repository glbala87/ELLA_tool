import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'
import template from './alleleSidebar.ngtmpl.html'

app.component('alleleSidebar', {
    templateUrl: 'alleleSidebar.ngtmpl.html',
    controller: connect(
        {
            expanded: state`views.workflows.alleleSidebar.expanded`,
            toggleExpanded: signal`views.workflows.alleleSidebar.toggleExpanded`
        },
        'AlleleSidebar'
    )
})
