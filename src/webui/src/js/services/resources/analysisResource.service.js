/* jshint esnext: true */

import {Service, Inject} from '../../ng-decorators';
import {Analysis} from '../../model/analysis';


@Service({
    serviceName: 'AnalysisResource'
})
@Inject('$resource')
class AnalysisResource {

    constructor(resource) {
        this.resource = resource;
    }

    get() {
        return new Promise((resolve, reject) => {
            var r = this.resource('/api/v1/analyses/', {}, {
                get: {
                    isArray: true
                }
            });
            var analyses = r.get(function () {
                let analyses_list = [];
                for (let analysis of analyses) {
                    analyses_list.push(new Analysis(analysis));
                }
                resolve(analyses_list);
            });
        });
    }
}

export default AnalysisResource;
