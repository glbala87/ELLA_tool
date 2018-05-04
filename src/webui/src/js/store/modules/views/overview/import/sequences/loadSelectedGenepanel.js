import { set, equals } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import getGenepanels from '../actions/getGenepanels'
import getGenepanel from '../actions/getGenepanel'
import toastr from '../../../../../common/factories/toastr'
import filterAndFlattenGenepanel from '../actions/filterAndFlattenGenepanel'

export default [
    set(props`genepanelName`, state`views.overview.import.selectedGenepanel.name`),
    set(props`genepanelVersion`, state`views.overview.import.selectedGenepanel.version`),
    // Optimization: If selected panel is same as default (which is already loaded), use that
    ({ state, props, path }) => {
        const defaultGenepanel = state.get('views.overview.import.data.defaultGenepanel')
        console.log(defaultGenepanel, props)
        if (
            defaultGenepanel.name === props.genepanelName &&
            defaultGenepanel.version === props.genepanelVersion
        ) {
            return path.sameasdefault()
        }
        return path.notsameasdefault()
    },
    {
        sameasdefault: [
            // Copy default panel to selected panel
            set(
                state`views.overview.import.data.genepanel`,
                state`views.overview.import.data.defaultGenepanel`
            )
        ],
        notsameasdefault: [
            getGenepanel,
            {
                success: [set(state`views.overview.import.data.genepanel`, props`result`)],
                error: [toastr('error', 'Failed to load genepanel')]
            }
        ]
    },
    filterAndFlattenGenepanel(
        'views.overview.import.data.genepanel',
        'views.overview.import.candidates.filteredFlattened',
        'views.overview.import.candidates.filter'
    ),
    set(state`views.overview.import.candidates.selectedPage`, 1)
]
