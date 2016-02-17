/* jshint esnext: true */

import {Service, Inject} from '../../ng-decorators';
import {Analysis} from '../../model/analysis';


@Service({
    serviceName: 'AnalysisResource'
})
@Inject('$resource')
class AnalysisResource {

    constructor(resource) {
        this.base = '/api/v1';
        this.resource = resource;
    }

    get() {
        return new Promise((resolve, reject) => {
            var r = this.resource(`${this.base}/analyses/`, {}, {
                get: {
                    isArray: true
                }
            });
            var analyses = r.get(function () {
                let analyses_list = [];
                for (let analysis of analyses) {
                    analyses_list.push(new Analysis(analysis));
                }
                resolve(analyses_list);
            });
        });
    }

    getAnalysis(id) {
        return new Promise((resolve, reject) => {
            var r = this.resource(`${this.base}/analyses/${id}/`);
            var analysis = r.get(() => {
                resolve(new Analysis(analysis));
            });
        });
    }

    markreview(id) {
        return new Promise((resolve, reject) => {
            let r = this.resource(`${this.base}/analyses/${id}/actions/markreview/`, {}, {
                complete: {
                    method: 'POST'
                }
            });
            r.complete(
                {
                    id: id
                },
                resolve(),
                reject()
            );
        });
    }

    finalize(id) {
        return new Promise((resolve, reject) => {
            let r = this.resource(`${this.base}/analyses/${id}/actions/finalize/`, {}, {
                finalize: {
                    method: 'POST'
                }
            });
            r.finalize(
                {
                    id: id
                },
                resolve(),
                reject()
            );
        });
    }

    override(id, user_id) {
        return new Promise((resolve, reject) => {
            let r = this.resource(`${this.base}/analyses/${id}/actions/override/`, {}, {
                override: {
                    method: 'POST'
                }
            });
            r.override(
                {
                    user_id: user_id
                },
                resolve,
                reject,
            );
        });
    }

    start(id, user_id) {
        return new Promise((resolve, reject) => {
            let r = this.resource(`${this.base}/analyses/${id}/actions/start/`, {}, {
                start: {
                    method: 'POST'
                }
            });
            r.start(
                {
                    user_id: user_id
                },
                resolve,
                reject
            );
        });
    }

    reopen(id, user_id) {
        return new Promise((resolve, reject) => {
            let r = this.resource(`${this.base}/analyses/${id}/actions/reopen/`, {}, {
                reopen: {
                    method: 'POST'
                }
            });
            r.reopen(
                {
                    user_id: user_id
                },
                resolve,
                reject
            );
        });
    }
}

export default AnalysisResource;
