/* jshint esnext: true */


import {Service, Inject} from '../ng-decorators';

@Service({
    serviceName: 'Config'
})
@Inject('$resource')
class ConfigService {

    constructor(resource) {
        this.resource = resource;
        this.config = null;
        this.overview = null;
    }

    /**
     * "Hack" that probably will bite me later:
     * Expect config to be loaded on startup,
     * then return cached object. Otherwise we have
     * to introduce Promises into everywhere in the app
     * where config is used...
     * Right now it's loaded in Analysis directive.
     */
    loadConfig() {
        return new Promise((resolve, reject) => {
            let r = this.resource('/api/v1/config/');
            let config = r.get(() => {
                this.config = config;
                this.overview = config.user.user_config.overview.views[0];
                resolve(config);
            });
        });
    }

    getConfig() {
        if (!this.config) {
            throw Error("Config not loaded, call loadConfig() first.");
        }
        return this.config;
    }

    setOverview(view) {
        this.overview = view;
    }

    getOverview() {
        return this.overview
    }
}
