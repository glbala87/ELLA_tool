/* jshint esnext: true */

import { Service, Inject } from '../../ng-decorators'
import { Interpretation } from '../../model/interpretation'
import { Allele } from '../../model/allele'
import Genepanel from '../../model/genepanel'

/**
 * - retrieve analyses
 * - drive analysis licecycle (start, finalize etc)
 */

@Service({
    serviceName: 'WorkflowResource'
})
@Inject('$resource')
class WorkflowResource {
    constructor(resource) {
        this.base = '/api/v1'
        this.resource = resource
        this.types = {
            allele: 'alleles',
            analysis: 'analyses'
        }
    }

    getInterpretation(type, id, interpretation_id) {
        return new Promise((resolve, reject) => {
            var AnalysisRS = this.resource(
                `${this.base}/workflows/${
                    this.types[type]
                }/${id}/interpretations/${interpretation_id}/`
            )
            var current_interpretation = AnalysisRS.get((data) => {
                resolve(new Interpretation(data))
            })
        })
    }

    getInterpretations(type, id) {
        return new Promise((resolve, reject) => {
            var AnalysisRS = this.resource(
                `${this.base}/workflows/${this.types[type]}/${id}/interpretations/`
            )
            var interpretations = AnalysisRS.query(() => {
                resolve(interpretations.map((i) => new Interpretation(i)))
            })
        })
    }

    getAlleles(type, id, interpretation_id, allele_ids, current_data = false) {
        return new Promise((resolve, reject) => {
            if (!allele_ids.length) {
                resolve([])
                return
            }
            var AnalysisRS = this.resource(
                `${this.base}/workflows/${
                    this.types[type]
                }/${id}/interpretations/${interpretation_id}/alleles/`,
                {
                    allele_ids: allele_ids.join(','),
                    current: current_data
                }
            )
            var alleles = AnalysisRS.query(() => {
                resolve(alleles.map((a) => new Allele(a)))
            }, reject)
        })
    }

    marknotready(
        type,
        id,
        annotations,
        custom_annotations,
        alleleassessments,
        referenceassessments,
        allelereports,
        attachments
    ) {
        return new Promise((resolve, reject) => {
            this._resourceWithAction(type, 'marknotready').doIt(
                { id },
                {
                    annotations: annotations,
                    custom_annotations: custom_annotations,
                    alleleassessments: alleleassessments,
                    referenceassessments: referenceassessments,
                    allelereports: allelereports,
                    attachments: attachments
                },
                resolve,
                reject
            )
        })
    }

    markinterpretation(
        type,
        id,
        annotations,
        custom_annotations,
        alleleassessments,
        referenceassessments,
        allelereports,
        attachments
    ) {
        return new Promise((resolve, reject) => {
            this._resourceWithAction(type, 'markinterpretation').doIt(
                { id },
                {
                    annotations: annotations,
                    custom_annotations: custom_annotations,
                    alleleassessments: alleleassessments,
                    referenceassessments: referenceassessments,
                    allelereports: allelereports,
                    attachments: attachments
                },
                resolve,
                reject
            )
        })
    }

    markreview(
        type,
        id,
        annotations,
        custom_annotations,
        alleleassessments,
        referenceassessments,
        allelereports,
        attachments
    ) {
        return new Promise((resolve, reject) => {
            this._resourceWithAction(type, 'markreview').doIt(
                { id },
                {
                    annotations: annotations,
                    custom_annotations: custom_annotations,
                    alleleassessments: alleleassessments,
                    referenceassessments: referenceassessments,
                    allelereports: allelereports,
                    attachments: attachments
                },
                resolve,
                reject
            )
        })
    }

    markmedicalreview(
        type,
        id,
        annotations,
        custom_annotations,
        alleleassessments,
        referenceassessments,
        allelereports,
        attachments
    ) {
        return new Promise((resolve, reject) => {
            this._resourceWithAction(type, 'markmedicalreview').doIt(
                { id },
                {
                    annotations: annotations,
                    custom_annotations: custom_annotations,
                    alleleassessments: alleleassessments,
                    referenceassessments: referenceassessments,
                    allelereports: allelereports,
                    attachments: attachments
                },
                resolve,
                reject
            )
        })
    }

    finalize(
        type,
        id,
        annotations,
        custom_annotations,
        alleleassessments,
        referenceassessments,
        allelereports,
        attachments
    ) {
        return new Promise((resolve, reject) => {
            this._resourceWithAction(type, 'finalize').doIt(
                { id },
                {
                    annotations: annotations,
                    custom_annotations: custom_annotations,
                    alleleassessments: alleleassessments,
                    referenceassessments: referenceassessments,
                    allelereports: allelereports,
                    attachments: attachments
                },
                resolve,
                reject
            )
        })
    }

    override(type, id) {
        return new Promise((resolve, reject) => {
            this._resourceWithAction(type, 'override').doIt({ id }, {}, resolve, reject)
        })
    }

    start(type, id, gp_name = null, gp_version = null) {
        return new Promise((resolve, reject) => {
            this._resourceWithAction(type, 'start').doIt(
                { id },
                {
                    gp_name: gp_name,
                    gp_version: gp_version
                },
                resolve,
                reject
            )
        })
    }

    reopen(type, id) {
        return new Promise((resolve, reject) => {
            this._resourceWithAction(type, 'reopen').doIt({ id }, {}, resolve, reject)
        })
    }

    patchInterpretation(type, id, interpretation) {
        return new Promise((resolve, reject) => {
            var AnalysesRS = this.resource(
                `${this.base}/workflows/${this.types[type]}/${id}/interpretations/${
                    interpretation.id
                }/`,
                {},
                {
                    update: {
                        method: 'PATCH'
                    }
                }
            )
            AnalysesRS.update(interpretation, resolve, reject)
        })
    }

    checkFinishAllowed(type, id, interpretation, sample_ids) {
        return new Promise((resolve, reject) => {
            // Finish is always allowed on alleles (for now)
            if (type === 'allele') {
                resolve()
                return
            }
            let url = `${this.base}/workflows/${this.types[type]}/${id}/interpretations/${
                interpretation.id
            }/finishallowed`
            if (sample_ids) {
                let q = JSON.stringify({ sample_ids: sample_ids })
                url += `?q=${encodeURIComponent(q)}`
            }

            let r = this.resource(url)
            r.get(() => {
                resolve()
            }, reject)
        })
    }

    getGenepanels(type, id) {
        if (type !== 'allele') {
            throw Error(`No way to fetch genepanels for type ${type}.`)
        }
        return new Promise((resolve, reject) => {
            var CollistionRS = this.resource(
                `${this.base}/workflows/${this.types[type]}/${id}/genepanels/`
            )
            var data = CollistionRS.query(() => {
                resolve(data)
            }, reject)
        })
    }

    getGenepanel(type, id, gp_name, gp_version) {
        return new Promise((resolve, reject) => {
            var GenepanelRS = this.resource(
                `${this.base}/workflows/${
                    this.types[type]
                }/${id}/genepanels/${gp_name}/${gp_version}/`
            )
            var data = GenepanelRS.get(() => {
                resolve(new Genepanel(data))
            }, reject)
        })
    }

    /**
     * Returns information about alleles that are currently being interpreted in
     * analyses _other_ than the provided analysis id, and which doesn't
     * have any existing alleleassessment.
     * @param  {int} id Analysis id
     * @return {Object}    Information about collisions
     */
    getCollisions(type, id) {
        return new Promise((resolve, reject) => {
            var CollistionRS = this.resource(
                `${this.base}/workflows/${this.types[type]}/${id}/collisions/`
            )
            var data = CollistionRS.query(() => {
                for (let d of data) {
                    d.allele = new Allele(d.allele)
                }
                resolve(data)
            }, reject)
        })
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
        return this.resource(
            `${this.base}/workflows/${this.types[type]}/:id/actions/:action/`,
            { action: action },
            { doIt: { method: 'POST' } }
        )
    }
}

export default WorkflowResource
