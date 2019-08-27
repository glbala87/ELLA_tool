import { set, equals } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import filterAndFlattenGenepanel from '../actions/filterAndFlattenGenepanel'
import batchFilterAndFlattenGenepanel from '../actions/batchFilterAndFlattenGenepanel'

export default [
    set(state`views.overview.import.custom.candidates.selectedPage`, 1),
    set(state`views.overview.import.custom.candidates.missingBatch`, []),
    equals(state`views.overview.import.custom.selectedFilterMode`),
    {
        single: [
            //set(state`views.overview.import.custom.candidates.filter`, props`filter`),
            //set(state`views.overview.import.custom.candidates.filterBatch`, ''),
            //set(state`views.overview.import.custom.candidates.filterBatchProcessed`, false),
            // If using single mode, reset batch mode to avoid inconsistent UI
            filterAndFlattenGenepanel(
                'views.overview.import.data.genepanel',
                'views.overview.import.custom.candidates.filteredFlattened',
                'views.overview.import.custom.candidates.filter'
            )
        ],
        batch: [batchFilterAndFlattenGenepanel],
        otherwise: []
    }
]
