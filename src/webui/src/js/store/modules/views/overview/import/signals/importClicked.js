import { set, when } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import postGenepanel from '../actions/postGenepanel'
import toastr from '../../../../../common/factories/toastr'
import postImportJob from '../actions/postImportJob'

export default [
    when(state`views.overview.import.customGenepanel`),
    {
        true: [
            set(props`genepanel`, state`views.overview.import.added.addedGenepanel`),
            postGenepanel,
            {
                success: [
                    postImportJob,
                    {
                        success: [],
                        error: [toastr('error', 'Failed to import sample')]
                    }
                ],
                error: [toastr('error', 'Failed to create genepanel')]
            }
        ],
        false: [
            set(props`genepanel`, state`views.overview.import.selectedGenepanel`),
            postImportJob,
            {
                success: [],
                error: [toastr('error', 'Failed to import sample')]
            }
        ]
    }
]
