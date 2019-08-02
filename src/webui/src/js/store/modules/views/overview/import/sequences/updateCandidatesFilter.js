import { set, when } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import filterAndFlattenGenepanel from '../actions/filterAndFlattenGenepanel'
import batchFilterAndFlattenGenepanel from '../actions/batchFilterAndFlattenGenepanel'

export default [
    set(state`views.overview.import.custom.candidates.selectedPage`, 1),
    set(state`views.overview.import.custom.candidates.missingBatch`, []),
    when(props`filter`, (t) => t !== undefined),
    {
        true: [
            set(state`views.overview.import.custom.candidates.filter`, props`filter`),
            // If using single mode, reset batch mode to avoid inconsistent UI
            set(state`views.overview.import.custom.candidates.filterBatch`, ''),
            set(state`views.overview.import.custom.candidates.filterBatchProcessed`, false),
            filterAndFlattenGenepanel(
                'views.overview.import.data.genepanel',
                'views.overview.import.custom.candidates.filteredFlattened',
                'views.overview.import.custom.candidates.filter'
            )
        ],
        false: []
    },
    when(props`filterBatch`, (t) => t !== undefined),
    {
        true: [
            // Reset single mode
            set(state`views.overview.import.custom.candidates.filter`, ''),
            set(state`views.overview.import.custom.candidates.filterBatch`, props`filterBatch`),
            batchFilterAndFlattenGenepanel
        ],
        false: []
    }
]
