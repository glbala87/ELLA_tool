import { when } from 'cerebral/operators'
import { props } from 'cerebral/tags'
import loadOverview from '../sequences/loadOverview'

const UPDATE_SECTIONS = ['analyses', 'variants', 'analyses-by-classified']

/**
 * Called by interval provider
 */
export default [
    ({ state }) => {
        // Get name of selected section
        const section = state.get('views.overview.state.selectedSection')
        if (UPDATE_SECTIONS.includes(section)) {
            return { section }
        }
        return {}
    },
    when(props`section`),
    {
        true: loadOverview,
        false: []
    }
]
