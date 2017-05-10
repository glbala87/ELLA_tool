/* jshint esnext: true */

import {Service, Inject} from '../../ng-decorators';
import Analysis from '../../model/analysis';
import {Allele} from '../../model/allele';

/**
 * - retrieve analyses
 * - drive analysis licecycle (start, finalize etc)
 */

@Service({
    serviceName: 'AnalysisResource'
})
@Inject('$resource')
class AnalysisResource {

    constructor(resource) {
        this.base = '/api/v1';
        this.resource = resource;
    }

    get() {
        return new Promise((resolve, reject) => {
            var AnalysisRS = this.resource(`${this.base}/analyses/`);
            var analyses = AnalysisRS.query(() => {
                resolve(analyses.map(a => new Analysis(a)));
            });
        });
    }

    getAnalysis(id) {
        return new Promise((resolve, reject) => {
            var AnalysisRS = this.resource(`${this.base}/analyses/${id}/`);
            var analysis = AnalysisRS.get(() => {
                resolve(new Analysis(analysis));
            });
        });
    }

}

export default AnalysisResource;
