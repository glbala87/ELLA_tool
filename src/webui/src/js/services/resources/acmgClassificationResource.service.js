/* jshint esnext: true */

import {Service, Inject} from '../../ng-decorators';


@Service({
    serviceName: 'ACMGClassificationResource'
})
@Inject('$resource')
class ACMGClassificationResource {

   constructor(resource) {
        this.resource = resource;
        this.base = '/api/v1';
    }

   getByAlleleIdsAndRefAssessmentIds(allele_ids, refassessment_ids, gp_name, gp_version) {
        return new Promise((resolve, reject) => {
            let r = this.resource(`${this.base}/acmg/alleles/?allele_ids=${allele_ids}&reference_assessment_ids=${refassessment_ids}&gp_name=${gp_name}&gp_version=${gp_version}`);
            let classification = r.get(
                () => {
                    resolve(classification);

                }
            );
        });
   }
}

export default ACMGClassificationResource;
