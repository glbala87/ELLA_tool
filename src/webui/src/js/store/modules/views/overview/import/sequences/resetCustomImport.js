import { sequence } from 'cerebral'
import prepareAddedGenepanel from '../actions/prepareAddedGenepanel'
import resetCustom from '../actions/resetCustom'
import filterAndFlattenGenepanel from '../actions/filterAndFlattenGenepanel'

export default sequence('resetCustomImport', [
    resetCustom,
    prepareAddedGenepanel,
    // Reset added view
    filterAndFlattenGenepanel(
        'views.overview.import.custom.added.addedGenepanel',
        'views.overview.import.custom.added.filteredFlattened',
        'views.overview.import.custom.added.filter'
    )
])
