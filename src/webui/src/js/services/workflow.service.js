/* jshint esnext: true */

import {Service, Inject} from '../ng-decorators';
import {AlleleStateHelper} from '../model/allelestatehelper';

/**
 * Controller for dialog asking user whether to markreview or finalize interpretation.
 */
class ConfirmCompleteInterpretationController {

    constructor(modalInstance) {
        this.modal = modalInstance;
    }
}


@Service({
    serviceName: 'Workflow'
})
@Inject('$rootScope',
        'Allele',
        'Analysis',
        'InterpretationResource',
        'User',
        '$uibModal',
        '$location')
class WorkflowService {

    constructor(rootScope,
        Allele,
        Analysis,
        interpretationResource,
        User,
        ModalService,
        LocationService) {


        //this._setWatchers(rootScope);
        this.analysisService = Analysis;
        this.alleleService = Allele;
        this.user = User;
        this.interpretationResource = interpretationResource;
        this.modalService = ModalService;
        this.locationService = LocationService;
    }

    loadInterpretation(id) {
        if (id === undefined) {
            throw Error("You must provide an id");
        }
        return new Promise((resolve, reject) => {
            let userPromise = this.user.getCurrentUser();
            let interpretationPromise = this.interpretationResource.get(id);

            // Prepare interpretation and assign user
            Promise.all([userPromise, interpretationPromise]).spread((user, interpretation) => {
                interpretation.analysis.type = 'singlesample'; // TODO: remove me when implemented in backend
                console.log("Interpretation loaded", interpretation);
                resolve(interpretation);
            });
        });
    }

    /**
     * Saves the current state to server.
     * If the status is 'Not started',
     * we start the interpretation before saving.
     * @return {Promise} Promise that resolves upon completion.
     */
    save(interpretation) {
        if (interpretation.status === 'Not started') {
            interpretation.user_id = this.user.getCurrentUserId();
            return this.analysisService.start(
                interpretation.analysis.id,
            ).then(
                () => {
                    interpretation.status = 'Ongoing';
                    // Update on server in case user made any changes
                    // before starting analysis.
                    return this.save(interpretation);
                }
            );
        }
        else {
            return this.interpretationResource.updateState(interpretation).then(
                () => interpretation.setClean()
            );
        }
    }

    /**
     * Popups a confirmation dialog, asking to complete or finalize the interpretation
     * @param  {Interpretation} interpretation
     * @param  {Array(Allele)} alleles  Alleles to include allele/referenceassessments for.
     * @return {Promise}  Resolves upon completed submission.
     */
    confirmCompleteFinalize(interpretation, alleles) {
        let modal = this.modalService.open({
            templateUrl: 'ngtmpl/interpretationConfirmation.modal.ngtmpl.html',
            controller: ['$uibModalInstance', ConfirmCompleteInterpretationController],
            size: 'lg',
            controllerAs: 'vm'
        });
        return modal.result.then(res => {
            // Save interpretation before marking as done
            if (res) {
                return this.save(interpretation).then(() => {
                    if (res === 'markreview') {
                        return this.analysisService.updateProperties(
                            interpretation.analysis.id,
                            interpretation.state.analysis.properties
                        ).then(() => {
                            this.analysisService.markreview(interpretation.analysis.id);
                        });
                    }
                    else if (res === 'finalize') {

                        // Collect info about this analysis.
                        let annotations = [];
                        let custom_annotations = [];
                        let alleleassessments = [];
                        let referenceassessments = [];
                        let allelereports = [];
                        // collection annotation ids for the alleles:
                        for (let allele_state of interpretation.state.allele) {
                            let match = alleles.find(a => a.id === allele_state.allele_id);

                            if (match) {
                                annotations.push({
                                    allele_id: match.id,
                                    annotation_id: match.annotation.annotation_id
                                });
                                if (match.annotation.custom_annotation_id) {
                                    custom_annotations.push({
                                        allele_id: match.id,
                                        custom_annotation_id: match.annotation.custom_annotation_id
                                    });
                                }
                            }
                        }

                        for (let allele_state of interpretation.state.allele) {
                            // Only include assessments/reports for alleles part of the supplied list.
                            // This is to avoid submitting assessments for alleles that have been
                            // removed from classification during interpretation process.
                            if (alleles.find(a => a.id === allele_state.allele_id)) {
                                alleleassessments.push(this.prepareAlleleAssessmentsForApi(
                                    allele_state.allele_id,
                                    allele_state,
                                    interpretation.analysis.id
                                    ));
                                referenceassessments = referenceassessments.concat(this.prepareReferenceAssessmentsForApi(
                                    allele_state,
                                    interpretation.analysis.id
                                ));
                                allelereports.push(this.prepareAlleleReportForApi(
                                    allele_state.allele_id,
                                    allele_state,
                                    interpretation.analysis.id
                                ));
                            }
                        }

                        return this.analysisService.updateProperties(
                            interpretation.analysis.id,
                            interpretation.state.analysis.properties
                        ).then(() => {
                            return this.analysisService.finalize(
                                interpretation.analysis.id,
                                annotations,
                                custom_annotations,
                                alleleassessments,
                                referenceassessments,
                                allelereports
                            );
                        });

                    }
                    else {
                        throw `Got unknown option ${res} when confirming interpretation action.`;
                    }
                });
            }
            return true;
        });
    }

    prepareAlleleAssessmentsForApi(allele_id, allelestate, analysis_id=null, genepanel_name=null, genepanel_version=null) {
        let assessment_data = {
            allele_id: allele_id,

        };
        if (analysis_id) {
            assessment_data.analysis_id = analysis_id;
        }
        if (genepanel_name &&
            genepanel_version) {
            assessment_data.genepanel_name = genepanel_name;
            assessment_data.genepanel_version = genepanel_version;
        }

        assessment_data.presented_alleleassessment_id = allelestate.presented_alleleassessment_id;
        if (AlleleStateHelper.isAlleleAssessmentReused(allelestate)) {
            assessment_data.reuse = true;
        } else {
            Object.assign(assessment_data, {
                user_id: this.user.getCurrentUserId(),
                classification: allelestate.alleleassessment.classification,
                evaluation: allelestate.alleleassessment.evaluation
            });
                }
        return assessment_data;
    }

    prepareReferenceAssessmentsForApi(allelestate, analysis_id=null, genepanel_name=null, genepanel_version=null) {
        let referenceassessments_data = [];
        if ('referenceassessments' in allelestate) {
            // Iterate over all referenceassessments for this allele
            for (let reference_state of allelestate.referenceassessments) {
                if (!reference_state.evaluation) {
                    continue;
                }
                let ra = {
                    reference_id: reference_state.reference_id,
                    allele_id: reference_state.allele_id
                };

                if (analysis_id) {
                    ra.analysis_id = analysis_id;
                }
                if (genepanel_name &&
                    genepanel_version) {
                    ra.genepanel_name = genepanel_name;
                    ra.genepanel_version = genepanel_version;
                }

                // If id is included, we're reusing an existing one.
                if ('id' in reference_state) {
                    ra.id = reference_state.id;
                }
                else {
                    // Fill in fields expected by backend
                    ra.evaluation = reference_state.evaluation || {};
                    ra.user_id = this.user.getCurrentUserId();
                }
                referenceassessments_data.push(ra);
            }
        }
        return referenceassessments_data;
    }

    prepareAlleleReportForApi(allele_id, allelestate, analysis_id=null, alleleassessment_id=null) {
        let report_data = {
            allele_id: allele_id,
        };
        if (analysis_id) {
            report_data.analysis_id = analysis_id;
        }
        if (alleleassessment_id) {
            report_data.alleleassessment_id = alleleassessment_id;
        }

        report_data.presented_allelereport_id = allelestate.presented_allelereport_id;
        // possible reuse:
        if (AlleleStateHelper.isAlleleReportReused(allelestate)) {
            report_data.reuse = true;
        } else {
            // Fill in fields expected by backend
            Object.assign(report_data, {
                user_id: this.user.getCurrentUserId(),
                evaluation: allelestate.allelereport.evaluation
            });
        }
        return report_data;
    }


}


export default WorkflowService;
