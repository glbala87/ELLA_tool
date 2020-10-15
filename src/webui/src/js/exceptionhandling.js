import { Inject, Run } from './ng-decorators'

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
