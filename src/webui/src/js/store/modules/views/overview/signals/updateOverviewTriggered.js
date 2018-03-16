import { parallel } from 'cerebral'
import { set } from 'cerebral/operators'
import { state, props, string } from 'cerebral/tags'
import loadOverview from '../sequences/loadOverview'

/**
 * Called by interval provider
 */
export default [
    ({ state }) => {
        // Get name of selected section
        return {
            section: Object.entries(state.get('views.overview.sections')).filter(
                e => e[1].selected
            )[0][0]
        }
    },
    loadOverview
]
