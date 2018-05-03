import { set, equals } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import prepareAddedGenepanel from '../actions/prepareAddedGenepanel'
import resetCustom from '../actions/resetCustom'
import filterGenepanel from '../actions/filterGenepanel'

export default [
    resetCustom,
    prepareAddedGenepanel,
    // Reset added view
    filterGenepanel(
        'views.overview.import.added.addedGenepanel',
        'views.overview.import.added.filteredGenepanel',
        'views.overview.import.added.filteredFlattened',
        'views.overview.import.added.filter'
    )
]
