/* jshint esnext: true */

import { Service, Inject } from '../../ng-decorators'
import { Allele } from '../../model/allele'
import Analysis from '../../model/analysis'

@Service({
    serviceName: 'AlleleResource'
})
@Inject('$resource')
export class AlleleResource {
    constructor(resource) {
        this.resource = resource
        this.base = '/api/v1'
    }

    get(allele_ids, sample_id = null, gp_name = null, gp_version = null, link_entities = null) {
        let q = { id: allele_ids }
        return this.getByQuery(q, sample_id, gp_name, gp_version, link_entities)
    }

    getGenepanels(allele_id) {
        return new Promise((resolve, reject) => {
            let GenepanelRS = this.resource(`${this.base}/alleles/:id/genepanels/`, {
                id: allele_id
            })
            let genepanels = GenepanelRS.query(() => {
                resolve(genepanels)
            }, reject)
        })
    }

    getAnalyses(allele_id) {
        return new Promise((resolve, reject) => {
            let AnalysesRS = this.resource(`${this.base}/alleles/:id/analyses/`, { id: allele_id })
            let analyses = AnalysesRS.query(() => {
                resolve(analyses.map((a) => new Analysis(a)))
            }, reject)
        })
    }
}
