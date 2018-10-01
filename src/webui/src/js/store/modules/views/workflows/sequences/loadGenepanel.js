import { sequence } from 'cerebral'
import { set, equals } from 'cerebral/operators'
import { state, props, string } from 'cerebral/tags'
import getGenepanel from '../actions/getGenepanel'

import toast from '../../../../common/factories/toast'

export default sequence('loadGenepanel', [
    getGenepanel,
    {
        error: [toast('error', 'Failed to load genepanel', 30000)],
        success: [set(state`views.workflows.data.genepanel`, props`result`)]
    }
])
