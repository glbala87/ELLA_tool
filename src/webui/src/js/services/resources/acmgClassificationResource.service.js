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

   getByAlleleIdsAndRefAssessmentIds(allele_ids, gp_name, gp_version, refassessment_ids=null) {
        let uri = `${this.base}/acmg/alleles/?allele_ids=${allele_ids}&gp_name=${gp_name}&gp_version=${gp_version}`;
        if (refassessment_ids) {
            uri += `&reference_assessment_ids=${refassessment_ids}`;
        }
        return new Promise((resolve, reject) => {
            let r = this.resource(uri);
            let classification = r.get(
                () => {
                    resolve(classification);

                }
            );
        });
   }
}

export default ACMGClassificationResource;
