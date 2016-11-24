/* jshint esnext: true */

import {Service, Inject} from '../../ng-decorators';
import {Allele} from '../../model/allele';

/**
 *
 * @param related_entities [{id: 1, allele_id: 3, presented_alleleleassessment_id: 8, ..}, ]
 * @returns {{assessment_id: Array, annotation_id: Array}} where assessment_id are gathered from the objects
 * in the input array
 */
function buildEntityMap(related_entities) {
    console.log("building a filter using");
    console.log(related_entities);

    let assessment_ids = [];
    let annotations_ids = [];
    for (let entry in related_entities) {
        let id = entry.presented_alleleassessment_id;

        let annotationId = entry.annotation_id;
        if (id) {
            assessment_ids.push(id);
        }
        if (annotationId) {
            annotations_ids.push(annotationId);
        }
    }

    var result = {
        'assessment_id': assessment_ids,
        'annotation_id': annotations_ids,
    };
    console.log(result);

    return result;
}

@Service({
    serviceName: 'AlleleResource'
})
@Inject('$resource')
export class AlleleResource {

    constructor(resource) {
        this.resource = resource;
        this.base = '/api/v1';
    }

    // related_entietes
    get(allele_ids, sample_id=null, gp_name=null, gp_version=null, related_entities=null) {
        return new Promise((resolve, reject) => {
            let uri = `${this.base}/alleles/`;
            // angular skips null parameters
            console.log(related_entities);

            let AlleleRS = this.resource(uri,
                { q: { 'id': allele_ids
                     },
                  a: related_entities ? buildEntityMap(related_entities): null,
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

