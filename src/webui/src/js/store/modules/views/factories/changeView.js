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
    interval('stop', 'views.overview.updateImportJobCountTriggered'),
    interval('stop', 'views.overview.updateOverviewTriggered')
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
            const previousView = state.get('views.current')
            state.set('views.current', key)

            // Reset other views' state when switching views.
            for (let view in VIEWS) {
                // Don't reset if pointing to same
                // or part of exempted views
                if (view !== key && !EXEMPT_RESET.includes(view)) {
                    state.set(`views.${view}`, {})
                    state.set(`views.__hasInit.${view}`, true)
                }
                if (
                    view === key &&
                    (!EXEMPT_RESET.includes(view) || !state.get(`views.__hasInit.${key}`))
                ) {
                    state.set(`views.${key}`, VIEWS[key]())
                    state.set(`views.__hasInit.${key}`, true)
                }
            }
        }
    ])
}

export default changeView
