/* jshint esnext: true */
import thenBy from 'thenby'

import { Service, Inject } from '../../ng-decorators'

@Service({
    serviceName: 'AlleleAssessmentResource'
})
@Inject('$resource')
class AlleleAssessmentResource {
    constructor(resource) {
        this.resource = resource
        this.base = '/api/v1'
    }

    getByAlleleIds(allele_ids) {
        return new Promise((resolve, reject) => {
            let q = JSON.stringify({
                date_superceeded: null,
                allele_id: allele_ids
            })
            let r = this.resource(`${this.base}/alleleassessments/?q=${encodeURIComponent(q)}`)
            let alleleassessments = r.query(() => {
                resolve(alleleassessments)
            }, reject)
        })
    }

    getHistoryForAlleleId(allele_id) {
        return new Promise((resolve, reject) => {
            let q = JSON.stringify({
                allele_id: allele_id
            })
            let r = this.resource(`${this.base}/alleleassessments/?q=${encodeURIComponent(q)}`)
            let alleleassessments = r.query(() => {
                resolve(alleleassessments.sort(thenBy((a) => a.date_created, -1)))
            }, reject)
        })
    }
}

export default AlleleAssessmentResource
