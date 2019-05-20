import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state } from 'cerebral/tags'
import { Compute } from 'cerebral'

import shouldShowSidebar from '../../store/modules/views/workflows/alleleSidebar/computed/shouldShowSidebar'
import template from './interpretation.ngtmpl.html'

app.component('interpretation', {
    templateUrl: 'interpretation.ngtmpl.html',
    controller: connect(
        {
            config: state`app.config`,
            sectionKeys: state`views.workflows.components.${state`views.workflows.selectedComponent`}.sectionKeys`,
            selectedComponent: state`views.workflows.selectedComponent`,
            showSidebar: shouldShowSidebar,
            selectedClassificationType: state`views.workflows.alleleSidebar.classificationType`,
            hasAlleles: Compute(state`views.workflows.interpretation.data.alleles`, (alleles) => {
                if (!alleles) {
                    return
                }
                return Object.keys(alleles).length
            })
        },
        'Interpretation'
    )
})
