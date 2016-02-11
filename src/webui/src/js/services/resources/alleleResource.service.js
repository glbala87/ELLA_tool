/* jshint esnext: true */

import {Service, Inject} from '../../ng-decorators';
import {Allele} from '../../model/allele';

@Service({
    serviceName: 'AlleleResource'
})
@Inject('$resource')
export class AlleleResource {

    constructor(resource) {
        this.resource = resource;
        this.base = '/api/v1';
    }

    get(allele_ids, sample_id=null, gp_name=null, gp_version=null, include_annotation=true) {
        return new Promise((resolve, reject) => {
            let q = JSON.stringify({
                'id': allele_ids
            });
            let uri = `${this.base}/alleles/?q=${encodeURIComponent(q)}`;
            if (sample_id !== null) {
                uri += `&sample_id=${sample_id}`
            }
            if (gp_name !== null && gp_version !== null) {
                uri += `&gp_name=${gp_name}&gp_version=${gp_version}`
            }
            let r = this.resource(uri);
            let alleles = r.query(() => {
                let alleles_obj = [];
                for (let allele of alleles) {
                    alleles_obj.push(new Allele(allele));
                }
                resolve(alleles_obj);
            }, reject);
        });
    }
}

