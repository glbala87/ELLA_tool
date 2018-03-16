import { sequence } from 'cerebral'
import getLoginState from '../login/getLoginState'
import getOverviewState from '../overview/getOverviewState'
import getWorkflowsState from '../workflows/getWorkflowsState'
import getDashboardState from '../dashboard/getDashboardState'
import { disableOnBeforeUnload } from '../../../common/factories/onBeforeUnload'
import interval from '../../../common/factories/interval'

const VIEWS = {
    overview: getOverviewState,
    login: getLoginState,
    workflows: getWorkflowsState,
    dashboard: getDashboardState
}

const EXEMPT_RESET = ['overview']

// Sequences to inject when changing a view
// Can be used to run view specific setup/resets
const PRE_SEQUENCES = {
    overview: null
}

const GLOBAL_PRE_SEQUENCE = [
    disableOnBeforeUnload(),
    interval('stop', 'views.overview.updateImportJobCountTriggered')
]

/**
 * Reset the state for all views except the provided key.
 * Use to avoid views leaving data in the state tree after
 * navigating to other views.
 */
function changeView(key) {
    return sequence('changeView', [
        GLOBAL_PRE_SEQUENCE,
        function changeView({ state }) {
            state.set('views.current', key)

            // Reset other views' state when switching views.
            for (let view in VIEWS) {
                // Don't reset if pointing to same
                // or part of exempted views
                if (view !== key && !EXEMPT_RESET.includes(view)) {
                    setTimeout(() => {
                        state.set(`views.${view}`, {})
                    }, 500) // Give view time to unmount before cleaning up
                }
                if (view === key) {
                    state.set(`views.${key}`, VIEWS[key]())
                }
            }
        }
    ])
}

export default changeView
