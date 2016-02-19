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
                dateSuperceeded: null,
                'allele_id': allele_ids,
                status: 1
            });
            let r = this.resource(`${this.base}/alleleassessments/?q=${encodeURIComponent(q)}`);
            let alleleassessments = r.query(() => {
                resolve(alleleassessments);
            });
        });
    }

    createOrUpdateAlleleAssessment(aa) {
        return new Promise(resolve => {
            let r = this.resource(`${this.base}/alleleassessments/`, {}, {createOrUpdate: {method: 'POST'}});
            r.createOrUpdate(aa, o => {
                resolve(o);
            });
        });
    }
}

export default AlleleAssessmentResource;
