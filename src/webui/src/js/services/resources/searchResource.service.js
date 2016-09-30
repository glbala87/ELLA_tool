/* jshint esnext: true */

import {Service, Inject} from '../../ng-decorators';
import {Allele} from '../../model/allele';
import Analysis from '../../model/analysis';


@Service({
    serviceName: 'SearchResource'
})
@Inject('$resource')
class SearchResource {

    constructor(resource) {
        this.resource = resource;
    }

    get(query) {
        return new Promise((resolve, reject) => {
            var r = this.resource(`/api/v1/search/?q=${encodeURIComponent(query)}`, {}, {
                get: {
                    isArray: false
                }
            });
            var result = r.get(function () {
                for (let item of result.alleles) {
                    let alleles = [];
                    for (let a of item.alleles) {
                        alleles.push(new Allele(a));
                    }
                    item.alleles = alleles;
                }
                for (let item of result.alleleassessments) {
                    let aa = [];
                    for (let a of item.alleles) {
                        aa.push(new Allele(a));
                    }
                    item.alleles = aa;
                }
                let analyses = [];
                for (let a of result.analyses) {
                    analyses.push(new Analysis(a));
                }
                result.analyses = analyses;
                resolve(result);
            }, reject);
        });
    }
}

export default SearchResource;
