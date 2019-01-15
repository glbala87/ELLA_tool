import { sequence } from 'cerebral'
import { set } from 'cerebral/operators'
import { props, state } from 'cerebral/tags'
import toast from '../../../../common/factories/toast'
import getReferences from '../actions/getReferences'

export default sequence('loadReferences', [
    getReferences,
    {
        success: [set(state`views.workflows.interpretation.data.references`, props`result`)],
        error: [toast('error', 'Failed to load references', 30000)]
    }
])
