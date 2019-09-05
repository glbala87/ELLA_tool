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
