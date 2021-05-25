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
const GLOBAL_PRE_SEQUENCE = [
    disableOnBeforeUnload(),
    interval('stop', 'views.overview.import.updateImportJobsTriggered'),
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
        function changeView({ state, props, http, execution }) {
            // Abort current http requests
            // Avoid if not properly propagated to backend. This will cause gunicorn backlog to fill up.
            // http.abort(/.*/)

            // Disable error handling of current running signals. This avoids logging (and toasting) exceptions when
            // they throw errors because of rapid navigation around the page.
            for (let exec of window.__cerebralRunningSignals) {
                if (exec.id !== execution.id) {
                    exec.errorCallback = () => {
                        return true
                    }
                    exec.__ignoreError = true
                }
            }

            state.set('views.current', key)
            // Reset other views' state when switching views.
            for (let view in VIEWS) {
                // Don't reset if pointing to same
                // or part of exempted views
                if (view !== key && !EXEMPT_RESET.includes(view)) {
                    state.set(`views.${view}`, {})
                    state.unset(`views.__hasInit.${view}`)
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
