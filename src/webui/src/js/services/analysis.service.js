/* jshint esnext: true */

import {Service, Inject} from '../ng-decorators';


@Service({
    serviceName: 'Analysis'
})
@Inject('$location',
        'Allele',
        'AnalysisResource',
        'InterpretationResource',
        'ReferenceResource',
        'User')
export class AnalysisService {

    constructor($location,
                Allele,
                AnalysisResource,
                InterpretationResource,
                ReferenceResource,
                User) {
        this.location = $location;
        this.alleleService = Allele;
        this.user = User;
        this.analysisResource = AnalysisResource;
        this.interpretationResource = InterpretationResource;
        this.referenceResource = ReferenceResource;
    }

    getAnalysis(analysis_id) {
        if (analysis_id === undefined) {
            throw Error("You must provide an id");
        }
        return this.analysisResource.getAnalysis(analysis_id);
    }

    updateProperties(analysis_id, properties) {
        return this.analysisResource.patch(
            analysis_id,
            {'properties': properties}
        );
    }

    getCollisions(id) {
        return this.analysisResource.getCollisions(id);
    }
}
