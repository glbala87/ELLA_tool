/* jshint esnext: true */

import {Service, Inject} from '../../ng-decorators';
import {Allele} from '../../model/allele';

/**
 * Collect the id of same entity types into an array, one array for each type.
 *
 * @param related_entities [{id: 1, allele_id: 3, presented_alleleleassessment_id: 8, ..}, ]
 * @returns {assessment_id: Array, annotation_id: Array} where assessment_id are gathered
 * from  'presented_alleleassessment_id'
 */
function buildEntityMap(related_entities) {
    let extracts = {  // see AnalysisFinalized
        'annotation_id': [],
        'customannotation_id': [],
        'presented_alleleassessment_id': [],
        'presented_allelereport_id': []
    };

    for (const extractKey of Object.keys(extracts)) {
        for (const entry of related_entities) {
            let id = entry[extractKey];
            if (id) {
                extracts[extractKey].push(id);
            }
        }
    }

    return  {
        'annotation_id': extracts['annotation_id'],
        'customannotation_id': extracts['customannotation_id'],
        'assessment_id': extracts['presented_alleleassessment_id'],
        'allelereport_id': extracts['presented_allelereport_id']
    };
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

    get(allele_ids, sample_id=null, gp_name=null, gp_version=null, link_entities=null) {
        let q = { 'id': allele_ids };
        return this.getByQuery(q, sample_id, gp_name, gp_version, link_entities);
    }

    getByQuery(query, sample_id=null, gp_name=null, gp_version=null, link_entities=null) {
        return new Promise((resolve, reject) => {
            let uri = `${this.base}/alleles/`;
            // angular skips null parameters
            let AlleleRS = this.resource(uri,
                { q: query,
                  link: link_entities ? buildEntityMap(link_entities): null,
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

    getAnalyses(allele_id) {
        return new Promise((resolve, reject) => {
            let AnalysesRS = this.resource(`${this.base}/alleles/:id/analyses/`, {id: allele_id});
            let analyses = AnalysesRS.query(() => {
                resolve(analyses);
            }, reject);
        });
    }
}

