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
                result.alleles = result.alleles.map(a => new Allele(a));

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
