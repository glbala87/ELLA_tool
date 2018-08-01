/* jshint esnext: true */

import { Service, Inject } from '../ng-decorators'

@Service({
    serviceName: 'Config'
})
@Inject('$resource')
class ConfigService {
    constructor(resource) {
        this.resource = resource
        this.config = null
        this.overview = null
    }

    setConfig(config) {
        this.config = config
    }

    getConfig() {
        if (!this.config) {
            throw Error('Config not loaded, call loadConfig() first.')
        }
        return this.config
    }
}
