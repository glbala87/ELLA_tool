import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import getGenepanel from '../actions/getGenepanel'
import toastr from '../../../../../common/factories/toastr'
import filterAndFlattenGenepanel from '../actions/filterAndFlattenGenepanel'

export default [
    set(props`genepanelName`, state`views.overview.import.selectedGenepanel.name`),
    set(props`genepanelVersion`, state`views.overview.import.selectedGenepanel.version`),
    getGenepanel,
    {
        success: [
            set(state`views.overview.import.data.genepanel`, props`result`),
            filterAndFlattenGenepanel(
                'views.overview.import.data.genepanel',
                'views.overview.import.candidates.filteredFlattened',
                'views.overview.import.candidates.filter'
            ),
            set(state`views.overview.import.candidates.selectedPage`, 1)
        ],
        error: [toastr('error', 'Failed to load genepanel')]
    }
]
