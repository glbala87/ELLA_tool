import { sequence } from 'cerebral'
import { set, equals } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import prepareAddedGenepanel from '../actions/prepareAddedGenepanel'
import resetCustom from '../actions/resetCustom'
import filterAndFlattenGenepanel from '../actions/filterAndFlattenGenepanel'

export default sequence('resetImport', [
    resetCustom,
    prepareAddedGenepanel,
    // Reset added view
    filterAndFlattenGenepanel(
        'views.overview.import.added.addedGenepanel',
        'views.overview.import.added.filteredFlattened',
        'views.overview.import.added.filter'
    )
])
