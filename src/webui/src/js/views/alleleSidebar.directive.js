import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'
import { Compute } from 'cerebral'
import template from './alleleSidebar.ngtmpl.html'

const showQuickClassificationBtn = Compute(
    state`views.workflows.selectedComponent`,
    (selectedComponent) => {
        return selectedComponent === 'Classification'
    }
)

app.component('alleleSidebar', {
    templateUrl: 'alleleSidebar.ngtmpl.html',
    controller: connect(
        {
            showQuickClassificationBtn,
            expanded: state`views.workflows.alleleSidebar.expanded`,
            toggleExpanded: signal`views.workflows.alleleSidebar.toggleExpanded`
        },
        'AlleleSidebar'
    )
})
