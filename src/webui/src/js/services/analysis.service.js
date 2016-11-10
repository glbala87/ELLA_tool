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

    markreview(analysis_id) {
        return this.analysisResource.markreview(analysis_id);
    }

    finalize(analysis_id, alleleassessments, referenceassessments, allelereports) {
        return this.analysisResource.finalize(
            analysis_id,
            alleleassessments,
            referenceassessments,
            allelereports
        );
    }

    start(analysis_id) {
        return this.analysisResource.start(analysis_id, this.user.getCurrentUserId());
    }

    reopen(analysis_id) {
        return this.analysisResource.reopen(analysis_id, this.user.getCurrentUserId());
    }

    override(analysis_id) {
        return this.analysisResource.override(analysis_id, this.user.getCurrentUserId());
    }

    openAnalysis(analysis_id) {
        this.location.path(`/analyses/${analysis_id}`);
    }

    openAnalysisList() {
        this.location.path('/analyses');
    }
}
