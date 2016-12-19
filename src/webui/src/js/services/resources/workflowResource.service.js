/* jshint esnext: true */

import {Service, Inject} from '../../ng-decorators';
import {Interpretation} from '../../model/interpretation';
import {Allele} from '../../model/allele';

/**
 * - retrieve analyses
 * - drive analysis licecycle (start, finalize etc)
 */

@Service({
    serviceName: 'WorkflowResource'
})
@Inject('$resource', 'User')
class WorkflowResource {

    constructor(resource, User) {
        this.base = '/api/v1';
        this.user = User;
        this.resource = resource;
    }

    getAnalysisCurrentInterpretations(analysis_id) {
        return new Promise((resolve, reject) => {
            var AnalysisRS = this.resource(`${this.base}/workflows/analyses/${analysis_id}/interpretations/current/`);
            var current_interpretation = AnalysisRS.get((data) => {
                resolve(new Interpretation(data));
            });
        });
    }

    getAnalysisInterpretations(analysis_id) {
        return new Promise((resolve, reject) => {
            var AnalysisRS = this.resource(`${this.base}/workflows/analyses/${analysis_id}/interpretations/`);
            var interpretations = AnalysisRS.query((data) => {
                resolve(data);
            });
        });
    }

    markreview(type, id) {
        return new Promise((resolve, reject) => {
            this._resourceWithAction(type, 'markreview').doIt(
                { id },
                {},
                resolve(),
                reject()
            );
        });
    }

    finalize(id, annotations, custom_annotations, alleleassessments, referenceassessments, allelereports) {

        return new Promise((resolve, reject) => {
            this._resourceWithAction(type, 'finalize').doIt(
                { id },
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

    override(type, id, user_id) {
        return new Promise((resolve, reject) => {
            this._resourceWithAction(type, 'override').doIt(
                { analysisId: id},
                {
                    user_id: user_id
                },
                resolve,
                reject,
            );
        });
    }

    start(type, id, user_id) {
        return new Promise((resolve, reject) => {
            this._resourceWithAction(type, 'start').doIt(
                { id },
                { user_id: user_id },
                resolve,
                reject
            );
        });
    }

    reopen(type, id, user_id) {
        return new Promise((resolve, reject) => {
            this._resourceWithAction(type, 'reopen').doIt(
                { id },
                { user_id: user_id },
                resolve,
                reject
            );
        });
    }

    patchInterpretation(type, id, data) {
        return new Promise((resolve, reject) => {
            let resource_types = {
                allele: 'alleles',
                analysis: 'analyses'
            };
            var AnalysesRS = this.resource(`${this.base}/workflows/${resource_types[type]}/${id}/interpretations/current/`, {}, {
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
    _resourceWithAction(type, action) {
        let resource_type = {
            allele: 'alleles',
            analysis: 'analyses'
        }
        return this.resource(`${this.base}/workflows/${resource_type[type]}/:id/actions/:action/`,
            { action: action },
            { doIt: { method: 'POST'} }
        );

    }

}

export default WorkflowResource;
