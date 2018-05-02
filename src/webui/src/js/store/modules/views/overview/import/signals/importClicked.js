import { set, when } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import postGenepanel from '../actions/postGenepanel'
import toastr from '../../../../../common/factories/toastr'

export default [
    when(state`views.overview.import.customGenepanel`),
    {
        true: [
            set(props`genepanel`, state`views.overview.import.added.addedGenepanel`),
            postGenepanel,
            {
                success: [],
                error: [toastr('error', 'Failed to create genepanel')]
            }
        ],
        false: []
    }
]
