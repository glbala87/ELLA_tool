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
