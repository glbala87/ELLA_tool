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

   getByAlleleIds(allele_ids, gp_name, gp_version, referenceassessments=null) {
        let uri = `${this.base}/acmg/alleles/`;

        let data = {
            allele_ids: allele_ids,
            gp_name: gp_name,
            gp_version: gp_version,
            referenceassessments: referenceassessments
        }
        return new Promise((resolve, reject) => {
            let r = this.resource(uri, null, {getCodes: {method: 'POST'}});
            let classification = r.getCodes(data, resolve, reject);
        });
   }
}

export default ACMGClassificationResource;
