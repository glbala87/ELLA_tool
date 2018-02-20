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
            var r = this.resource(`/api/v1/search/?q=${encodeURIComponent(JSON.stringify(query))}`, {}, {
                get: {
                    isArray: false
                }
            });
            var result = r.get(function () {
                result.alleles = result.alleles.map(a => {
                    a.allele = new Allele(a.allele)
                    return a
                });

                let analyses = [];
                for (let a of result.analyses) {
                    analyses.push(new Analysis(a));
                }
                result.analyses = analyses;
                resolve(result);
            }, reject);
        });
    }

    getOptions(query) {
        return new Promise((resolve, reject) => {
            if (!query) {
                resolve([])
            }
            var r = this.resource(`/api/v1/search/options/?q=${encodeURIComponent(JSON.stringify(query))}`, {}, {
                get: {
                    isArray: false
                }
            });
            var result = r.get(function () {
                resolve(result);
            }, reject);
        });
    }

}

export default SearchResource;
