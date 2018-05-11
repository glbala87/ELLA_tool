import { sequence } from 'cerebral'
import { set, equals } from 'cerebral/operators'
import { state, props, string } from 'cerebral/tags'
import getReferences from '../actions/getReferences'
import toastr from '../../../../common/factories/toastr'

export default sequence('loadReferences', [
    getReferences,
    {
        success: [set(state`views.workflows.data.references`, props`result`)],
        error: [toastr('error', 'Failed to load references', 30000)]
    }
])
