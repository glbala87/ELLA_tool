import { sequence } from 'cerebral'
import { set, equals } from 'cerebral/operators'
import { state, props, string } from 'cerebral/tags'
import getCollisions from '../actions/getCollisions'

import toastr from '../../../../common/factories/toastr'

export default sequence('loadCollisions', [
    getCollisions,
    {
        error: [toastr('error', 'Failed to load collisions', 5000)],
        success: [set(state`views.workflows.collisions`, props`result`)]
    }
])
