import { sequence } from 'cerebral'
import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import getAnnotationConfigs from '../../../actions/getAnnotationConfigs'
import { classificationSectionContent } from '../../../actions/prepareComponents'
import toast from '../../../../../../common/factories/toast'

export default sequence('loadAnnotationConfigs', [
    getAnnotationConfigs(`views.workflows.modals.addExcludedAlleles.data.alleles`),
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
