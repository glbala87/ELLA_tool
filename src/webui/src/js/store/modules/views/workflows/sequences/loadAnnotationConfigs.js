import { sequence } from 'cerebral'
import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import getAnnotationConfigs from '../actions/getAnnotationConfigs'
import toast from '../../../../common/factories/toast'

export default sequence('loadAnnotationConfigs', [
    getAnnotationConfigs(`views.workflows.interpretation.data.alleles`),
    {
        success: [set(state`views.workflows.data.annotationConfigs`, props`result`)],
        error: [toast('error', 'Failed to load annotation configs')]
    }
])
