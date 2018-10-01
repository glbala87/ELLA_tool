import { set, when } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import postGenepanel from '../actions/postGenepanel'
import toast from '../../../../../common/factories/toast'
import postImportJob from '../actions/postImportJob'
import resetCustomImport from '../sequences/resetCustomImport'

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
                        success: [
                            resetCustomImport,
                            set(state`views.overview.import.selectedSample`, null),
                            toast('success', 'Import job created.', 5000)
                        ],
                        error: [toast('error', 'Failed to import sample')]
                    }
                ],
                error: [toast('error', 'Failed to create genepanel. Maybe name exists already?')]
            }
        ],
        false: [
            set(props`genepanel`, state`views.overview.import.selectedGenepanel`),
            postImportJob,
            {
                success: [
                    set(state`views.overview.import.selectedSample`, null),
                    toast('success', 'Import job created.', 5000)
                ],
                error: [toast('error', 'Failed to import sample')]
            }
        ]
    }
]
