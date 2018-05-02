import { set, equals } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import loadSelectedGenepanel from './loadSelectedGenepanel'
import loadDefaultGenepanel from './loadDefaultGenepanel'
import prepareAddedGenepanel from '../actions/prepareAddedGenepanel'
import filterGenepanel from '../actions/filterGenepanel'

export default [
    loadDefaultGenepanel,
    prepareAddedGenepanel,
    loadSelectedGenepanel,
    // Reset added view
    filterGenepanel(
        'views.overview.import.added.addedGenepanel',
        'views.overview.import.added.filteredGenepanel',
        'views.overview.import.added.filteredFlattened',
        'views.overview.import.added.filter'
    )
]
