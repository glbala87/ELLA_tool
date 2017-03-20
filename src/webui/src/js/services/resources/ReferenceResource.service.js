/* jshint esnext: true */

import {Reference} from '../../model/reference';
import {Service, Inject} from '../../ng-decorators';

@Service({
    serviceName: 'ReferenceResource'
})
@Inject('$resource')
class ReferenceResource {

    constructor(resource) {
        this.resource = resource;
        this.base = '/api/v1';
    }

    createFromXml(xml) {
        let data = {
            xml
        }
        return new Promise((resolve, reject) => {
            let r = this.resource(`${this.base}/references/`, {}, {create: {method: 'POST'}});
            r.create(data, o => {
                resolve(o);
            }, reject);
        });
    }

    getByPubMedIds(pmids) {
        return new Promise((resolve, reject) => {
            if (!pmids.length) {
                resolve([]);
            }
            let q = JSON.stringify({'pubmed_id': pmids});
            let r = this.resource(`${this.base}/references/?q=${encodeURIComponent(q)}`);
            let references = r.query(() => {
                let refs = [];
                for (let o of references) {
                    refs.push(new Reference(o));
                }
                resolve(refs);
            });
        });
    }

    getReferenceAssessments(allele_ids, reference_ids) {
        let q = JSON.stringify({
            date_superceeded: null,
            'allele_id': allele_ids,
            'reference_id': reference_ids,
            status: 1
        });
        return new Promise(resolve => {
            let r = this.resource(`${this.base}/referenceassessments/?q=${encodeURIComponent(q)}`);
            let result = r.query(() => {
                resolve(result);
            });
        });
    }

    createOrUpdateReferenceAssessment(ra) {
        return new Promise(resolve => {
            let r = this.resource(`${this.base}/referenceassessments/`, {}, {createOrUpdate: {method: 'POST'}});
            r.createOrUpdate(ra, o => {
                resolve(o);
            });
        });
    }

    search(searchString) {
        return new Promise(resolve => {
            if (searchString.length < 3) {
                resolve([]);
            }
            else {
                let s = JSON.stringify({'search_string': searchString});
                let r = this.resource(`${this.base}/references/?s=${encodeURIComponent(s)}&num_per_page=${encodeURIComponent("10")}`);
                let references = r.query(() => {
                    let refs = [];
                    for (let o of references) {
                        refs.push(new Reference(o));
                    }
                    resolve(refs);
                });
            }
        })
    }


}

export default ReferenceResource;
