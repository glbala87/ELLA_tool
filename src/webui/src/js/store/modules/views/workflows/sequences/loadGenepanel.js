import { sequence } from 'cerebral'
import { set, equals } from 'cerebral/operators'
import { state, props, string } from 'cerebral/tags'
import getGenepanel from '../actions/getGenepanel'

import toastr from '../../../../common/factories/toastr'

export default sequence('loadGenepanel', [
    getGenepanel,
    {
        error: [toastr('error', 'Failed to load genepanel', 30000)],
        success: [set(state`views.workflows.data.genepanel`, props`result`)]
    }
])
