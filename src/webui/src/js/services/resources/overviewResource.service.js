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
                for (let key of ['marked_review', 'missing_alleleassessment', 'ongoing', 'finalized']) {
                    for (let item of data[key]) {
                        item.allele = new Allele(item.allele);
                    }
                }

                resolve(overview);
            }, reject);
        });
    }

    getAnalysesOverview() {
        return new Promise((resolve, reject) => {
            let uri = `${this.base}/overviews/analyses/`;
            let r = this.resource(uri);
            let overview = r.get((data) => {

                for (let key of ['with_findings', 'without_findings', 'missing_alleleassessments', 'ongoing', 'marked_review', 'finalized']) {
                    let analyses_objs = [];
                    for (let a of data[key]) {
                        analyses_objs.push(new Analysis(a));
                    }
                    data[key] = analyses_objs;
                }

                resolve(overview);
            }, reject);
        });
    }

}

