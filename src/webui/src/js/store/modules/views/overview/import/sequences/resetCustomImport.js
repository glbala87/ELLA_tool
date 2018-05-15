import { sequence } from 'cerebral'
import prepareAddedGenepanel from '../actions/prepareAddedGenepanel'
import resetCustom from '../actions/resetCustom'
import filterAndFlattenGenepanel from '../actions/filterAndFlattenGenepanel'

export default sequence('resetCustomImport', [
    resetCustom,
    prepareAddedGenepanel,
    // Reset added view
    filterAndFlattenGenepanel(
        'views.overview.import.added.addedGenepanel',
        'views.overview.import.added.filteredFlattened',
        'views.overview.import.added.filter'
    )
])
