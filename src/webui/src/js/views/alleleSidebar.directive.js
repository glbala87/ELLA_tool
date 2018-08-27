import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'
import { Compute } from 'cerebral'
import template from './alleleSidebar.ngtmpl.html'
import isExpanded from '../store/modules/views/workflows/alleleSidebar/computed/isExpanded'

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
            expanded: isExpanded,
            toggleExpanded: signal`views.workflows.alleleSidebar.toggleExpanded`
        },
        'AlleleSidebar'
    )
})
