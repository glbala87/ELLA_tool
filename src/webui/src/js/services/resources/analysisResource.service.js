/* jshint esnext: true */

import {Service, Inject} from '../../ng-decorators';
import Analysis from '../../model/analysis';

/**
 * - retrieve analyses
 * - drive analysis licecycle (start, finalize etc)
 */

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
            var AnalysisRS = this.resource(`${this.base}/analyses/`);
            var analyses = AnalysisRS.query(() => {
                resolve(analyses.map(a => new Analysis(a)));
            });
        });
    }

    getAnalysis(id) {
        return new Promise((resolve, reject) => {
            var AnalysisRS = this.resource(`${this.base}/analyses/${id}/`);
            var analysis = AnalysisRS.get(() => {
                resolve(new Analysis(analysis));
            });
        });
    }

    markreview(id) {
        return new Promise((resolve, reject) => {
            this._resourceWithAction('markreview').doIt(
                { analysisId: id },
                {},
                resolve(),
                reject()
            );
        });
    }

    finalize(id, annotations, custom_annotations, alleleassessments, referenceassessments, allelereports) {

        return new Promise((resolve, reject) => {
            this._resourceWithAction('finalize').doIt(
                { analysisId: id },
                {
                    user_id: this.user.getCurrentUserId(),
                    annotations: annotations,
                    custom_annotations: custom_annotations,
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
            this._resourceWithAction('override').doIt(
                { analysisId: id},
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
            this._resourceWithAction('start').doIt(
                { analysisId: id },
                { user_id: user_id },
                resolve,
                reject
            );
        });
    }

    reopen(id, user_id) {
        return new Promise((resolve, reject) => {
            this._resourceWithAction('reopen').doIt(
                { analysisId: id },
                { user_id: user_id },
                resolve,
                reject
            );
        });
    }

    patch(id, data) {
        return new Promise((resolve, reject) => {
            var AnalysesRS = this.resource(`${this.base}/analyses/${id}/`, {}, {
                update: {
                    method: 'PATCH'
                }
            });
            AnalysesRS.update(
                data,
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
            var CollistionRS = this.resource(`${this.base}/analyses/${id}/collisions/`);
            var data = CollistionRS.query(() => {
                for (let user of data) {
                    user.alleles = user.alleles.map(a => new Allele(a));
                }
                resolve(data);
            }, reject);
        });
    }

    /**
     * Usage:
     *  let MyResource = _resourceWithAction('reopen', 4);
     *  MyResource.doIt(..)
     *
     * @param action
     * @param analysisId
     * @returns an Angular Resource class with a custom action 'doIt'
     * @private
     */
    _resourceWithAction(action) {
        return this.resource(`${this.base}/analyses/:analysisId/actions/:action/`,
            { action: action },
            { doIt: { method: 'POST'} }
        );

    }

}

export default AnalysisResource;
