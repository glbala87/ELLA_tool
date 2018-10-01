import { sequence } from 'cerebral'
import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import getCollisions from '../actions/getCollisions'

import toast from '../../../../common/factories/toast'

export default sequence('loadCollisions', [
    getCollisions,
    {
        error: [toast('error', 'Failed to load collisions', 5000)],
        success: [set(state`views.workflows.data.collisions`, props`result`)]
    }
])
