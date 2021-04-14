import { Inject, Run, app } from './ng-decorators'

export default class ExceptionHandling {
    @Run()
    @Inject('cerebral')
    init(cerebral) {
        if (window) {
            window.onerror = (message, source, lineno, colno, error) => {
                const err = {
                    name: error.name,
                    message: error.message,
                    stack: error.stack || null
                }
                cerebral.controller.getSignal('app.logException')({ error: err })
            }
            window.__cerebralRunningSignals = []
            cerebral.controller.on('start', (execution, payload) => {
                // Keep track of running signals to properly handle their exceptions.
                // If a signal is interrupted by a changeView, error should be expected, and
                // it should not show toast or log exception to backend
                window.__cerebralRunningSignals.push(execution)
            })
            cerebral.controller.on('end', (execution, payload) => {
                // Remove signal from window.
                // Note the additional check to remove long-running signals (older than 1 minute).
                // We assume they are zombies that never trigger 'end'
                // Worst case, they will trigger 'end', and possibly raise an unsuppressed exception
                window.__cerebralRunningSignals = window.__cerebralRunningSignals.filter(
                    (x) => x.id != execution.id || x.datetime < Date.now() - 60000
                )
            })
        }
    }
}

// Error handling: Log errors to backend
app.factory('$exceptionHandler', [
    '$log',
    function($log) {
        return function myExceptionHandler(exception, cause) {
            // HACK: We need to load cerebral dependency dynamically
            // to avoid circular imports
            const cerebral = angular
                .element(document.body)
                .injector()
                .get('cerebral')
            const err = {
                name: exception.name,
                message: exception.message,
                stack: exception.stack || null
            }
            cerebral.controller.getSignal('app.logException')({ error: err })
            $log.error(exception, cause)
        }
    }
])
