/* jshint esnext: true */

import {Service, Inject} from '../../ng-decorators';
import Analysis from '../../model/analysis';
import {Allele} from '../../model/allele';


@Service({
    serviceName: 'AnalysisResource'
})
@Inject('$resource', 'User')
class AnalysisResource {

    constructor(resource, User) {
        this.base = '/api/v1';
        this.user = User;
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

    patch(id, data) {
        return new Promise((resolve, reject) => {
            var r = this.resource(`${this.base}/analyses/${id}/`, {}, {
                update: {
                    method: 'PATCH'
                }
            });
            r.update(
                data,
                resolve,
                reject
            );
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
                resolve,
                reject
            );
        });
    }

    finalize(id, alleleassessments, referenceassessments, allelereports) {
        return new Promise((resolve, reject) => {
            let r = this.resource(`${this.base}/analyses/${id}/actions/finalize/`, {}, {
                finalize: {
                    method: 'POST'
                }
            });
            r.finalize(
                {
                    user_id: this.user.getCurrentUserId(),
                    alleleassessments: alleleassessments,
                    referenceassessments: referenceassessments,
                    allelereports: allelereports
                },
                resolve,
                reject
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

    /**
     * Returns information about alleles that are currently being interpreted in
     * analyses _other_ than the provided analysis id, and which doesn't
     * have any existing alleleassessment.
     * @param  {int} id Analysis id
     * @return {Object}    Information about collisions
     */
    getCollisions(id) {
        return new Promise((resolve, reject) => {
            var r = this.resource(`${this.base}/analyses/${id}/collisions/`);
            var data = r.query(() => {
                for (let user of data) {
                    user.alleles = user.alleles.map(a => new Allele(a));
                }
                resolve(data);
            }, reject);
        });
    }
}

export default AnalysisResource;
