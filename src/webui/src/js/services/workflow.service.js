/* jshint esnext: true */

import {Service, Inject} from '../ng-decorators';
import {AlleleStateHelper} from '../model/allelestatehelper';

/**
 * Controller for dialog asking user whether to markreview or finalize interpretation.
 */
class ConfirmCompleteInterpretationController {

    constructor(canFinalize, modalInstance) {
        this.canFinalize = canFinalize;
        this.modal = modalInstance;
    }
}


@Service({
    serviceName: 'Workflow'
})
@Inject('$rootScope',
        'Allele',
        'WorkflowResource',
        '$uibModal',
        '$location')
class WorkflowService {

    constructor(rootScope,
        Allele,
        WorkflowResource,
        ModalService,
        LocationService) {


        //this._setWatchers(rootScope);
        this.alleleService = Allele;
        this.workflowResource = WorkflowResource;
        this.modalService = ModalService;
        this.locationService = LocationService;
    }

    markreview(type, id, interpretation, alleles) {

        let prepared_data = this.prepareInterpretationForApi(type, id, interpretation, alleles);
        return this.workflowResource.markreview(
            type,
            id,
            prepared_data.annotations,
            prepared_data.custom_annotations,
            prepared_data.alleleassessments,
            prepared_data.referenceassessments,
            prepared_data.allelereports,
            prepared_data.attachments
        );
    }

    finalize(type, id, interpretation, alleles) {

        let prepared_data = this.prepareInterpretationForApi(type, id, interpretation, alleles);
        return this.workflowResource.finalize(
            type,
            id,
            prepared_data.annotations,
            prepared_data.custom_annotations,
            prepared_data.alleleassessments,
            prepared_data.referenceassessments,
            prepared_data.allelereports,
            prepared_data.attachments
        );
    }

    start(type, id, gp_name=null, gp_version=null) {
        return this.workflowResource.start(type, id, gp_name, gp_version);
    }

    reopen(type, id) {
        return this.workflowResource.reopen(type, id);
    }

    override(type, id) {
        return this.workflowResource.override(type, id);
    }

    /**
     * Saves the current state to server.
     * @return {Promise} Promise that resolves upon completion.
     */
    save(type, id, interpretation) {
        if (interpretation.status === 'Not started') {
            throw Error("Interpretation not started");
        }
        else {
            return this.workflowResource.patchInterpretation(type, id, interpretation).then(
                () => interpretation.setClean()
            );
        }
    }

    /**
     * Loads in allele data from backend, including ACMG data.
     * Referenceassessments and included alleles are fetched from interpretation's state.
     *
     */
    loadAlleles(type, id, interpretation, current_data=false) {
        // Clone allele_ids array
        let allele_ids = interpretation.allele_ids.slice(0);

        // Add any manually added alleles
        if ('manuallyAddedAlleles' in interpretation.state) {
            // First clean the state, since previously manually added might now not be
            // part of the excluded ones. This can happen when a user had included
            // a previously filtered allele, and then given it a classification.
            interpretation.state.manuallyAddedAlleles = interpretation.state.manuallyAddedAlleles.filter(m => {
                return Object.values(interpretation.excluded_allele_ids).some(excluded => {
                    return excluded.includes(m);
                });
            });
            allele_ids = allele_ids.concat(interpretation.state.manuallyAddedAlleles);
        }

        return this.workflowResource.getAlleles(
            type,
            id,
            interpretation.id,
            allele_ids,
            current_data
        ).then(
            alleles => {
            // Flatten all referenceassessments from state
            let referenceassessments = [];
            if ('allele' in interpretation.state) {
                referenceassessments = Object.values(interpretation.state.allele).map(
                    al => al.referenceassessments
                ).reduce((p, c) => {
                    if (c) {
                        return p.concat(c.filter(e => e.evaluation));
                    }
                    return p;
                }, []);
            }
            if (alleles.length) {
                // Updates allele.acmg inplace
                return this.alleleService.updateACMG(
                    alleles,
                    interpretation.genepanel_name,
                    interpretation.genepanel_version,
                    referenceassessments
                ).then(() => alleles);
            }
            else {
                return alleles;
            }
        });
    }

    /**
     * Checks whether user is allowed to finalize the analysis.
     * Criteria is that every allele must:
     *  - have an alleleassessment with a classification.
     *  - if the classification is reused it must not be outdated
     *
     * @return {bool}
     */
    canFinalize(interpretation, alleles, config) {
        if (!alleles) {
            return false;
        }
        if (alleles.length === 0) {
            return true;
        }
        // Ensure that we have an interpretation with a state
        if (interpretation &&
            interpretation.status === 'Ongoing' &&
            'allele' in interpretation.state) {

                // Check that all alleles
                // - have classification
                // - if reused, that they're not outdated
                return alleles.every(a => {
                    if (a.id in interpretation.state.allele) {
                        let allele_state = interpretation.state.allele[a.id];
                        let has_classification = Boolean(AlleleStateHelper.getClassification(a, allele_state));
                        let not_reused_outdated = true;
                        if (AlleleStateHelper.isAlleleAssessmentReused(allele_state)) {
                            not_reused_outdated = !AlleleStateHelper.isAlleleAssessmentOutdated(a, config);
                        }
                        return has_classification && not_reused_outdated;
                    }
                });
            }

        return false;
    }

    /**
     * Popups a confirmation dialog, asking to complete or finalize the interpretation
     * @param  {Interpretation} interpretation
     * @param  {Array(Allele)} alleles  Alleles to include allele/referenceassessments for.
     * @return {Promise}  Resolves upon completed submission.
     */
    confirmCompleteFinalize(type, id, interpretation, alleles, config) {
        let modal = this.modalService.open({
            templateUrl: 'ngtmpl/interpretationConfirmation.modal.ngtmpl.html',
            controller: ['canFinalize', '$uibModalInstance', ConfirmCompleteInterpretationController],
            size: 'lg',
            resolve: {
                canFinalize: () => this.canFinalize(interpretation, alleles, config)
            },
            controllerAs: 'vm'
        });
        return modal.result.then(res => {
            // Save interpretation before marking as done
            // FIXME:
            /*return this.analysisService.updateProperties(
                    interpretation.analysis.id,
                    interpretation.state.analysis.properties
            )*/
            if (res) {
                return this.save(type, id, interpretation).then(() => {
                    if (res === 'markreview') {
                        return this.markreview(type, id, interpretation, alleles);
                    }
                    else if (res === 'finalize') {
                        return this.finalize(type, id, interpretation, alleles);
                    }
                    else {
                        throw `Got unknown option ${res} when confirming interpretation action.`;
                    }
                });
            }
            return true;
        });
    }

    prepareInterpretationForApi(type, id, interpretation, alleles) {
        // Collect info about this interpretation.
        let annotations = [];
        let custom_annotations = [];
        let alleleassessments = [];
        let referenceassessments = [];
        let allelereports = [];
        let attachments = [];

        // collection annotation ids for the alleles:
        for (let allele_state of Object.values(interpretation.state.allele)) {
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

        for (let allele_state of Object.values(interpretation.state.allele)) {
            // Only include assessments/reports for alleles part of the supplied list.
            // This is to avoid submitting assessments for alleles that have been
            // removed from classification during interpretation process.
            let found_allele = alleles.find(a => a.id === allele_state.allele_id);
            if (found_allele) {
                alleleassessments.push(this.prepareAlleleAssessmentsForApi(
                    found_allele,
                    allele_state,
                    type === 'analysis' ? id : null,
                    interpretation.genepanel_name,
                    interpretation.genepanel_version
                    ));
                referenceassessments = referenceassessments.concat(this.prepareReferenceAssessmentsForApi(
                    allele_state,
                    type === 'analysis' ? id : null,
                    interpretation.genepanel_name,
                    interpretation.genepanel_version
                ));
                allelereports.push(this.prepareAlleleReportForApi(
                    found_allele,
                    allele_state,
                    type === 'analysis' ? id : null
                ));

                attachments.push({"allele_id": allele_state.allele_id, "attachments": allele_state.alleleassessment.attachments})
            }
        }

        return {
            annotations,
            custom_annotations,
            alleleassessments,
            referenceassessments,
            allelereports,
            attachments,
        }
    }

    prepareAlleleAssessmentsForApi(allele, allelestate, analysis_id=null, genepanel_name=null, genepanel_version=null) {
        let assessment_data = {
            allele_id: allele.id,

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
                }
                referenceassessments_data.push(ra);
            }
        }
        return referenceassessments_data;
    }

    prepareAlleleReportForApi(allele, allelestate, analysis_id=null, alleleassessment_id=null) {

        let report_data = {
            allele_id: allele.id,
        };
        if (analysis_id) {
            report_data.analysis_id = analysis_id;
        }
        if (alleleassessment_id) {
            report_data.alleleassessment_id = alleleassessment_id;
        }

        report_data.presented_allelereport_id = allelestate.presented_allelereport_id;

        // possible reuse:
        if (allelestate.allelereport
            && allele.allele_report
            && angular.toJson(allelestate.allelereport.evaluation) == angular.toJson(allele.allele_report.evaluation)) {
            report_data.reuse = true;
        } else {
            report_data.reuse = false;
            // Fill in fields expected by backend
            Object.assign(report_data, {
                evaluation: allelestate.allelereport.evaluation
            });
        }
        return report_data;
    }


}


export default WorkflowService;
