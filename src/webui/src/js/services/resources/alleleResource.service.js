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

    get(allele_ids, sample_id=null, gp_name=null, gp_version=null, include_annotation=true, related_entities=null) {
        return new Promise((resolve, reject) => {
            let uri = `${this.base}/alleles/`;
            // angular skips null parameters
            let AlleleRS = this.resource(uri,
                { q: { 'id': allele_ids
                     },
                  // TODO: populate the x with values from parameter related_entities
                  // x: { 'annotation_id': [],
                  //      'custom_annotation_id': [],
                  //      'assessment_id': [2],
                  //      'reference_assessment_id': [],
                  //      'report_id': []
                  //    },
                  sample_id: sample_id,
                  gp_name: gp_name,
                  gp_version: gp_version
                });
            let alleles = AlleleRS.query(() => {
                resolve(alleles.map(a => new Allele(a)));
            }, reject);
        });
    }

    getGenepanels(allele_id) {
        return new Promise((resolve, reject) => {
            let GenepanelRS = this.resource(`${this.base}/alleles/:id/genepanels/`, {id: allele_id});
            let genepanels = GenepanelRS.query(() => {
                resolve(genepanels);
            }, reject);
        });
    }
}

