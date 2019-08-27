import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import getGenepanel from '../actions/getGenepanel'
import toast from '../../../../../common/factories/toast'
import filterAndFlattenGenepanel from '../actions/filterAndFlattenGenepanel'
import updateCandidatesFilter from './updateCandidatesFilter'

export default [
    set(props`genepanelName`, state`views.overview.import.selectedGenepanel.name`),
    set(props`genepanelVersion`, state`views.overview.import.selectedGenepanel.version`),
    getGenepanel,
    {
        success: [
            set(state`views.overview.import.data.genepanel`, props`result`),
            updateCandidatesFilter
        ],
        error: [toast('error', 'Failed to load genepanel')]
    }
]
