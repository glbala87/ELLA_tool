import { set, equals, when } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import postGenepanel from '../actions/postGenepanel'
import toast from '../../../../../common/factories/toast'
import postImportJob from '../actions/postImportJob'
import resetCustomImport from '../sequences/resetCustomImport'
import loadImportJobs from '../sequences/loadImportJobs'

const preparePostPayload = ({ props, state }) => {
    const selectedSample = state.get('views.overview.import.selectedSample')
    const priority = state.get('views.overview.import.priority')
    const { name, version } = props.genepanel
    const payload = {
        sample_id: selectedSample.name,
        genepanel_name: name,
        genepanel_version: version,
        properties: {
            priority: priority
        }
    }
    return { importJob: payload }
}

const commonOnSuccess = [toast('success', 'Import job created.', 5000), loadImportJobs]

export default [
    equals(state`views.overview.import.importSourceType`),
    {
        user: [
            postImportJob,
            {
                success: commonOnSuccess,
                error: [toast('error', 'Failed to submit imports')]
            }
        ],
        sample: [
            when(state`views.overview.import.customGenepanel`),
            {
                true: [
                    set(props`genepanel`, state`views.overview.import.custom.added.addedGenepanel`),
                    postGenepanel,
                    {
                        success: [
                            preparePostPayload,
                            postImportJob,
                            {
                                success: [
                                    resetCustomImport,
                                    set(state`views.overview.import.selectedSample`, null),
                                    commonOnSuccess
                                ],
                                error: [toast('error', 'Failed to import sample')]
                            }
                        ],
                        error: [
                            toast('error', 'Failed to create genepanel. Maybe name exists already?')
                        ]
                    }
                ],
                false: [
                    set(props`genepanel`, state`views.overview.import.selectedGenepanel`),
                    preparePostPayload,
                    postImportJob,
                    {
                        success: [
                            set(state`views.overview.import.selectedSample`, null),
                            commonOnSuccess
                        ],
                        error: [toast('error', 'Failed to import sample')]
                    }
                ]
            }
        ]
    }
]
