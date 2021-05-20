import { sequence } from 'cerebral'
import { set, concat, merge } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
// src/webui/src/js/store/modules/views/workflows/modals/addExcludedAlleles/sequences/loadAnnotationConfigs.js
// src/webui/src/js/store/modules/views/workflows/actions/getAnnotationConfigs.js
import getAnnotationConfigs from '../../../actions/getAnnotationConfigs'
import { classificationSectionContent } from '../../../actions/prepareComponents'
import toast from '../../../../../../common/factories/toast'

export default sequence('loadAnnotationConfigs', [
    getAnnotationConfigs(state`views.workflows.modals.addExcludedAlleles.data.alleles`),
    {
        success: [
            set(
                state`views.workflows.modals.addExcludedAlleles.data.annotationConfigs`,
                props`result`
            )
        ],
        error: [toast('error', 'Failed to load annotation configs')]
    },
    set(
        state`views.workflows.modals.addExcludedAlleles.sectionContent`,
        classificationSectionContent(
            state`views.workflows.modals.addExcludedAlleles.data.alleles`,
            state`views.workflows.modals.addExcludedAlleles.data.annotationConfigs`
        )
    )
])
