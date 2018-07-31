import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'
import { Compute } from 'cerebral'

import isReadOnly from '../../store/modules/views/workflows/computed/isReadOnly'
import shouldShowSidebar from '../../store/modules/views/workflows/alleleSidebar/computed/shouldShowSidebar'
import template from './interpretation.ngtmpl.html'

app.component('interpretation', {
    template,
    controller: connect(
        {
            config: state`app.config`,
            sectionKeys: state`views.workflows.components.${state`views.workflows.selectedComponent`}.sectionKeys`,
            selectedComponent: state`views.workflows.selectedComponent`,
            showSidebar: shouldShowSidebar,
            hasAlleles: Compute(state`views.workflows.data.alleles`, (alleles) => {
                if (!alleles) {
                    return
                }
                return Object.keys(alleles).length
            })
        },
        'Interpretation'
    )
})
