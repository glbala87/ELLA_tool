/* jshint esnext: true */

import {Service, Inject} from '../ng-decorators';
/**
 * Controller for dialog asking user whether to complete or finalize interpretation.
 */
class ConfirmCompleteInterpretationController {

    constructor(modalInstance, complete, finalize) {
        this.modal = modalInstance;
    }
}


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

    markreview(analysis_id) {
        return this.analysisResource.markreview(analysis_id);
    }

    finalize(analysis_id) {
        return this.analysisResource.finalize(analysis_id);
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

    createOrUpdateReferenceAssessment(analysis, ra_state, allele, reference) {

        return this.alleleService.createOrUpdateReferenceAssessment(
            ra_state,
            allele,
            reference,
            analysis.genepanel.name,
            analysis.genepanel.version,
            analysis.id
        ).then(o => {
            this.alleleService.updateACMG(
                [allele],
                analysis.genepanel.name,
                analysis.genepanel.version
            );
            return o;
        });
    }

    createOrUpdateAlleleAssessment(analysis, aa_state, allele) {
        return this.alleleService.createOrUpdateAlleleAssessment(
            aa_state,
            allele,
            analysis.genepanel.name,
            analysis.genepanel.version,
            analysis.id
        );
    }

    openAnalysis(analysis_id) {
        this.location.path(`/analyses/${analysis_id}`);
    }

    openAnalysisList() {
        this.location.path('/analyses');
    }
}
