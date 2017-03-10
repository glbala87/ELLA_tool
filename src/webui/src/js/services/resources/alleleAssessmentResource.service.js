/* jshint esnext: true */

import {Service, Inject} from '../../ng-decorators';

@Service({
    serviceName: 'AlleleAssessmentResource'
})
@Inject('$resource')
class AlleleAssessmentResource {

    constructor(resource) {
        this.resource = resource;
        this.base = '/api/v1';
    }

    getByAlleleIds(allele_ids) {
        return new Promise((resolve, reject) => {
            let q = JSON.stringify({
                date_superceeded: null,
                'allele_id': allele_ids
            });
            let r = this.resource(`${this.base}/alleleassessments/?q=${encodeURIComponent(q)}`);
            let alleleassessments = r.query(() => {
                resolve(alleleassessments);
            }, reject);
        });
    }

    getHistoryForAlleleId(allele_id) {
        return new Promise((resolve, reject) => {
            let q = JSON.stringify({
                'allele_id': allele_id
            });
            let r = this.resource(`${this.base}/alleleassessments/?q=${encodeURIComponent(q)}`);
            let alleleassessments = r.query(() => {
                resolve(
                    alleleassessments.sort(firstBy(a => a.date_created, -1))
                );
            }, reject);
        });
    }

    createOrUpdateAlleleAssessment(aa) {
        return new Promise((resolve, reject) => {
            let r = this.resource(`${this.base}/alleleassessments/`, {}, {createOrUpdate: {method: 'POST', isArray: true}});
            r.createOrUpdate(aa, resolve, reject);
        });
    }

    createOrUpdateAlleleReport(ar) {
        return new Promise((resolve, reject) => {
            let r = this.resource(`${this.base}/allelereports/`, {}, {createOrUpdate: {method: 'POST', isArray: true}});
            r.createOrUpdate(ar, resolve, reject);
        });
    }
}

export default AlleleAssessmentResource;
