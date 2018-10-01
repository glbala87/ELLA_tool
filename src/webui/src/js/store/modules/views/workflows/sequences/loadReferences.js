import { sequence } from 'cerebral'
import { set, equals } from 'cerebral/operators'
import { state, props, string } from 'cerebral/tags'
import getReferences from '../actions/getReferences'
import toast from '../../../../common/factories/toast'

export default sequence('loadReferences', [
    getReferences,
    {
        success: [set(state`views.workflows.data.references`, props`result`)],
        error: [toast('error', 'Failed to load references', 30000)]
    }
])
