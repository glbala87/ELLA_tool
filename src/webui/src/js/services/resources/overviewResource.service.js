/* jshint esnext: true */

import {Service, Inject} from '../../ng-decorators';
import {Allele} from '../../model/allele';
import Analysis from '../../model/analysis';

@Service({
    serviceName: 'OverviewResource'
})
@Inject('$resource')
export class OverviewResource {

    constructor(resource) {
        this.resource = resource;
        this.base = '/api/v1';
    }

    getAllelesOverview() {
        return new Promise((resolve, reject) => {
            let uri = `${this.base}/overviews/alleles/`;
            let r = this.resource(uri);
            let overview = r.get((data) => {

                // Convert to our model objects
                for (let key of ['marked_review', 'missing_alleleassessment']) {
                    for (let item of data.alleles[key]) {
                        item.allele = new Allele(item.allele);
                    }
                }

                for (let key of ['with_findings', 'without_findings', 'missing_alleleassessments']) {
                    let analyses_objs = [];
                    for (let a of data.analyses[key]) {
                        analyses_objs.push(new Analysis(a));
                    }
                    data.analyses[key] = analyses_objs;
                }

                resolve(overview);
            }, reject);
        });
    }

}

