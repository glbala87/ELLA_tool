import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import batchFilterAndFlattenGenepanel from '../actions/batchFilterAndFlattenGenepanel'

export default [
    set(state`views.overview.import.custom.candidates.filterBatch`, props`filterBatch`),
    batchFilterAndFlattenGenepanel
]
