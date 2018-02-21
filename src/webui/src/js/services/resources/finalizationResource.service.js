/* jshint esnext: true */

import { Service, Inject } from '../../ng-decorators'
import Analysis from '../../model/analysis'
import { Allele } from '../../model/allele'

/**
 *  retrieve data used as basis for a finalized analysis
 *
 */

@Service({
    serviceName: 'FinalizationService'
})
@Inject('$resource')
class FinalizationResource {
    constructor(resource) {
        this.base = '/api/v1'
        this.resource = resource
    }

    /**
     * See schema AnalysisFinalized
     * @param analysis_id
     * @returns {Promise} [{id: 1, allele_id: 4, presented_alleleassessment_id: 3, annotation_id: 89,...},
     */
    get(analysis_id) {
        return new Promise((resolve, reject) => {
            var FinalizationRS = this.resource(`${this.base}/analyses/finalized/${analysis_id}/`)
            var finals = FinalizationRS.query(() => {
                let fs = []
                for (let f of finals) {
                    fs.push(f)
                }
                resolve(fs)
            })
        })
    }
}

export default FinalizationResource
