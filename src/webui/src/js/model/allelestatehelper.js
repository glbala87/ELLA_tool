/* jshint esnext: true */

import {deepCopy} from '../util';

export class AlleleStateHelper {

    static checkAlleleStateModel(allele_state) {
        // We need to check every key for itself, as we can have older, partial models as input

        if (!('alleleassessment' in allele_state)) {
            allele_state.alleleassessment = {}
        }

        let alleleassesment = allele_state.alleleassessment;
        if (!('reuse' in alleleassesment)) {
            alleleassesment.reuse = false;
        }

        if (!('classification' in alleleassesment)) {
            alleleassesment.classification = null;
        }

        if (!('evaluation' in alleleassesment)) {
            alleleassesment.evaluation = {};
        }

        if (!('attachment_ids' in alleleassesment)) {
            alleleassesment.attachment_ids = [];
        }

        let evaluation = alleleassesment.evaluation;
        for (let key of ['prediction', 'classification', 'external', 'frequency', 'reference']) {
            if (!(key in evaluation)) {
                evaluation[key] = {
                    comment: ''
                };
            }
        }

        if (!('acmg' in evaluation)) {
            evaluation.acmg = {
                included: [],
                suggested: []
            }
        }

        if (!('referenceassessments' in allele_state)) {
            allele_state.referenceassessments = [];
        }

        if (!('allelereport' in allele_state)) {
            allele_state.allelereport = {
                evaluation: {
                    comment: ''
                }
            };
        }

        if (!('verification' in allele_state)) {
            allele_state.verification = null;
        }
    }

    /**
     * Helper class for working with alleleState objects
     * (alleleState objects are part of the interpretation's state,
     * describing the state for one allele).
    */

    static setupAlleleState(allele, allele_state) {
        // If not existing, return the object from the state, or create empty one

        this.checkAlleleStateModel(allele_state);
        if (allele.allele_assessment) {
            allele_state.presented_alleleassessment_id = allele.allele_assessment.id;
        }

        if (allele.allele_report) {
            allele_state.presented_allelereport_id = allele.allele_report.id;
        }

        this.copyAlleleAssessmentToState(allele, allele_state);
        this.copyAlleleReportToState(allele, allele_state);

    }

    /**
     * Returns classification for allele, either by using
     * classification from state or by be existing allele_assessment
     * if alleleassessment is reused.
     * @param  {Allele} allele   Allele to get existing alleleassessment
     * @param  {Object} allele_state   Allele state to modify
     * @return  {String} Classification for given allele
     */
    static getClassification(allele, allele_state) {
        let aa = this.getAlleleAssessment(allele, allele_state);
        if ('classification' in aa) {
            return aa.classification;
        }
        else {
            return null;
        }
    }

    /**
     * Returns alleleassessment data for allele, either by using
     * alleleassessment from state or by be existing allele_assessment
     * if alleleassessment is reused.
     * @param  {Allele} allele   Allele to get existing alleleassessment
     * @param  {Object} allele_state   Allele state to modify
     * @return  {Object} allleleassessment data
     */
    static getAlleleAssessment(allele, allele_state) {
        // Ensure object is properly initialised
        this.setupAlleleState(allele, allele_state);
        if (this.isAlleleAssessmentReused(allele_state)) {
            if (!('allele_assessment' in allele)) {
                throw Error("Alleleassessment set as reused, but there's no allele_assessment in provided allele.");
            }
            return allele.allele_assessment;
        }
        else {
            return allele_state.alleleassessment;
        }
    }

    static getReusedAlleleAssessment(allele, allele_state) {
        if (this.isAlleleAssessmentReused(allele_state)) {
            if (!('allele_assessment' in allele)) {
                throw Error("Alleleassessment set as reused, but there's no allele_assessment in provided allele.");
            }
            return allele.allele_assessment;
        }
    }

    static getStateAlleleAssessment(allele, allele_state) {
        this.setupAlleleState(allele, allele_state);
        return allele_state.alleleassessment;
    }

    static getStateReferenceAssessment(allele, reference, allele_state) {
        if ('referenceassessments' in allele_state) {
            return allele_state.referenceassessments.find(
                ra => ra.allele_id === allele.id &&
                      ra.reference_id === reference.id
            );
        }
    }

    static getExistingReferenceAssessment(allele, reference) {
        if (allele.reference_assessments) {
            return allele.reference_assessments.find(ra => ra.reference_id === reference.id);
        }
    }

    static hasReferenceAssessment(allele, reference, allele_state) {
        let a = this.getExistingReferenceAssessment(allele, reference)
        let b = this.getStateReferenceAssessment(allele, reference, allele_state)
        return !(
            (a === undefined || a.evaluation.relevance === undefined)
            && (b === undefined || b.evaluation === undefined || b.evaluation.relevance === undefined)
        )

    }

    /**
     * Returns referemceassessment data for allele + reference, either by using
     * referenceassessment from state or by the existing allele.reference_assessments.
     * Existing referenceassessments are reused by default, i.e. the first time
     * this function is called and there are no existing data in the state for this
     * allele + reference, any existing referenceassessments will be returned
     * (and it's id added to state).
     * @param  {Allele} allele   Allele to get existing referenceassessment
     * @param  {Reference} reference   Reference to get existing referenceassessment
     * @param  {Object} allele_state   Allele state to modify
     * @return  {Object} referenceassessment data
     */
    static getReferenceAssessment(allele, reference, allele_state) {

        if (!('referenceassessments' in allele_state)) {
            allele_state.referenceassessments = [];
        }

        let state_ra = this.getStateReferenceAssessment(allele, reference, allele_state);

        // No refassessment object in state -> either set to reuse existing
        // if it's present or create template object
        if (!state_ra) {

            state_ra = {
                allele_id: allele.id,
                reference_id: reference.id,
            };

            let existing = this.getExistingReferenceAssessment(allele, reference);
            if (existing) {
                // Set as reused
                state_ra.id = existing.id;
                // Return copy to avoid mutating source
                allele_state.referenceassessments.push(state_ra);
                return this.getExistingReferenceAssessment(allele, reference);
            }
            else {
                // Prepare object
                state_ra.evaluation = {};
                allele_state.referenceassessments.push(state_ra);
                return state_ra;
            }
        }
        // Exists in state, check if it is set to reused and if so,
        // return the existing object
        else if ('id' in state_ra) {
            return this.getExistingReferenceAssessment(allele, reference);
        }
        // Exists in state, but not reused -> return the state object
        else {
            return state_ra;
        }
    }

    /**
     * Returns allelereport data for allele, either by using
     * allelereport from state or by be existing allele_report
     * if alleleassessment is reused.
     * @param  {Allele} allele   Allele to get existing allelereport
     * @param  {Object} allele_state   Allele state to modify
     * @return  {Object} allelereport data
     */
    static getAlleleReport(allele, allele_state) {
        if (this.isAlleleReportReused(allele_state)) {
            if (!('allele_report' in allele)) {
                throw Error("AlleleReport set as reused, but there's no allele_report in provided allele.");
            }
            // Should only happen for legacy alleles without allelereport data.
            if (!('allele_report' in allele)) {
                return {};
            }
            return allele.allele_report;
        }
        else {
            if (!('allelereport' in allele_state)) { // TODO: remove if checkAlleleStateModel covers this case
                allele_state.allelereport = {
                    evaluation: {}
                }
            }
            return allele_state.allelereport;
        }
    }

    /**
     * Updates the classification of an allele
     * @param  {Object} allele_state   Allele state to modify
     * @param  {String} classification Classification to set
     */
    static updateClassification(allele_state, classification) {
        allele_state.alleleassessment.classification = classification;
    }

    /**
     * Updates the referenceassessment of an allele + reference
     * @param  {Allele} allele   Allele object to get id from
     * @param  {Reference} reference   Reference object to get id from
     * @param  {Object} allele_state   Allele state to modify
     * @param  {String} referenceassessment Referenceassessment data
     */
    static updateReferenceAssessment(allele, reference, allele_state, referenceassessment) {
        // Find state data
        let state_ra = allele_state.referenceassessments.find(
            ra => ra.allele_id === allele.id &&
                  ra.reference_id === reference.id
        );
        // Update the object with new data, and remove the reuse ('id')
        Object.assign(state_ra, referenceassessment);
        delete state_ra.id;
    }

    /**
     * Copies any existing allele's alleleassessment into the allele_state.
     * To be used when the user want's to edit the existing assessment.
     * @param {Allele} allele   Allele to copy alleleassessment from.
     * @param {Object} allele_state   Allele state to modify
     * @param {Boolean} force_copy Copy into allele_state regardless
     */
    static copyAlleleAssessmentToState(allele, allele_state, force_copy=false) {
        // Check if remote alleleassessment is newer, if so copy it in again.
        if (allele.allele_assessment &&
             (force_copy ||
              (!allele_state.alleleAssessmentCopiedFromId ||
               allele.allele_assessment.id > allele_state.alleleAssessmentCopiedFromId)
             )
            ) {
            allele_state.alleleassessment.evaluation = deepCopy(allele.allele_assessment.evaluation);
            allele_state.alleleassessment.attachment_ids = deepCopy(allele.allele_assessment.attachment_ids)
            allele_state.alleleassessment.classification = allele.allele_assessment.classification;
            allele_state.alleleAssessmentCopiedFromId = allele.allele_assessment.id;
            // The copied alleleassessment can have an older model that is lacking fields.
            // We need to check the model and add any missing fields to make it up to date.
            this.checkAlleleStateModel(allele_state);
        }
    }

    /**
     * Copies any existing allele's report into the allele_state.
     * To be used when the user want's to edit the existing report.
     * @param {Allele} allele   Allele to copy report from.
     * @param {Object} allele_state   Allele state to modify
     * @param {Boolean} force_copy Copy into allele_state regardless
     */
    static copyAlleleReportToState(allele, allele_state, force_copy=false) {
        // Check if date of remote allelereport is newer, if so copy it in again.
        // TODO: Present dialog for confirmation.
        if (allele.allele_report &&
            (force_copy ||
             (!allele_state.alleleReportCopiedFromId ||
              allele.allele_report.id > allele_state.alleleReportCopiedFromId)
            )
           ) {
            allele_state.allelereport.evaluation = deepCopy(allele.allele_report.evaluation);
            allele_state.alleleReportCopiedFromId = allele.allele_report.id;
        }
    }

    /**
     * Enables reusing the existing classification of allele.
     * If alleleassessment is outdated, it refuse to toggle on.
     * @param  {Allele} allele   Allele to reuse alleleassessment of.
     * @param  {Object} allele_state   Allele state to modify
     * @param  {Config}  config Application config
     * @return {Boolean}              Whether toggle is true or not
     */
    static enableReuseAlleleAssessment(allele, allele_state, config) {
        if (!('allele_assessment' in allele)) {
            throw Error("Cannot reuse alleleassessment from allele without existing alleleassessment");
        }
        this.setupAlleleState(allele, allele_state);


        // Check whether existing allele assessment is outdated,
        // if so refuse to toggle on.
        if (this.isAlleleAssessmentOutdated(allele, config)) {
            return false;
        }

        if ('allele_assessment' in allele) {
            allele_state.presented_alleleassessment_id = allele.allele_assessment.id;
            allele_state.alleleassessment.reuse = true;
        }

        return true;
    }

    /**
     * Disables reusing the existing classification of allele.
     * If alleleassessment is outdated, it refuse to toggle on.
     * @param  {Allele} allele   Allele to reuse alleleassessment of.
     * @param  {Object} allele_state   Allele state to modify
     * @return {Boolean}              Whether toggle is true or not
     */
    static disableReuseAlleleAssessment(allele, allele_state) {
        this.setupAlleleState(allele, allele_state);

        allele_state.alleleassessment.reuse = false;

        return false;
    }

    /**
     * Toggles reusing the existing classification of allele.
     * If alleleassessment is outdated, it refuse to toggle on.
     * @param  {Allele} allele   Allele to reuse alleleassessment of.
     * @param  {Object} allele_state   Allele state to modify
     * @param  {Config}  config Application config
     * @return {Boolean}              Whether toggle is true or not
     */
    static toggleReuseAlleleAssessment(allele, allele_state, config) {
        if (this.isAlleleAssessmentReused(allele_state)) {
            return this.disableReuseAlleleAssessment(allele, allele_state);
        }
        else {
            return this.enableReuseAlleleAssessment(allele, allele_state, config);
        }
    }

    /**
     *  Auto-reuse new, existing alleleassessment for the user.
     *  We keep track of last alleleassessment id where we auto-reused the alleleassessment,
     *  in order to prevent re-enabling what the user has already disabled.
     *
     *  Returns whether existing assessment was reused.
     */
    static autoReuseExistingAssessment(allele, allele_state, config) {
        if (allele.allele_assessment) {
            // Check whether it's outdated, if so force disabling reuse.
            if (this.isAlleleAssessmentOutdated(allele, config)) {
                this.disableReuseAlleleAssessment(allele, allele_state);
                return false;
            }
            else if (!('autoReuseAlleleAssessmentCheckedId' in allele_state) ||
                allele_state.autoReuseAlleleAssessmentCheckedId < allele.allele_assessment.id) {
                if (!this.isAlleleAssessmentOutdated(allele, config)) {
                    this.enableReuseAlleleAssessment(allele, allele_state, config)
                    allele_state.autoReuseAlleleAssessmentCheckedId = allele.allele_assessment.id;
                }
                return true;
            }
        }
        return false;
    }

    static addAlleleToReport(allele_state) {
        if (!('report' in allele_state)) {
            allele_state.report = {};
        }
        allele_state.report.included = true;

    }

    static removeAlleleFromReport(allele_state) {
        if (!('report' in allele_state)) {
            allele_state.report = {};
        }
        allele_state.report.included = false;

    }

    /**
     * For automatically adding certain classifications to the report (e.g. class 3, 4, 5 alleles).
     *
     * @param {Allele} allele
     * @param {Object} allele_state
     * @param {Object} config
     */
    static checkAddRemoveAlleleToReport(allele, allele_state, config) {
        let classification = this.getClassification(allele, allele_state);
        let config_option = config.classification.options.find(o => {
            return o.value === classification;
        });
        if (config_option &&
            config_option.include_report &&
            allele_state.verification !== 'technical'
        ) {
            this.addAlleleToReport(allele_state);
        }
        else {
            // Either include_report option is not set, or classification is null
            this.removeAlleleFromReport(allele_state);
        }
    }

    static isAlleleAssessmentReused(allele_state) {
        return allele_state && allele_state.alleleassessment && allele_state.alleleassessment.reuse;
    }
    static isAlleleReportReused(allele_state) {
        return allele_state && allele_state.allelereport && allele_state.allelereport.reuse;
    }

    /**
     * Checks whether the allele's existing allele_assessment is outdated.
     * TODO: Doesn't strictly belong here, but we need it in this module.
     * @param  {Allele}  allele Allele's allele assessment to check.
     * @param  {Config}  config Application config
     * @return {Boolean}        Whether the assessment is outdated.
     */
    static isAlleleAssessmentOutdated(allele, config) {
        if (!allele.allele_assessment) {
            return false;
        }
        let classification = allele.allele_assessment.classification;
        // Find classification from config
        let option = config.classification.options.find(o => o.value === classification);
        if (option === undefined) {
            throw Error(`Classification ${classification} not found in configuration.`);
        }
        if ('outdated_after_days' in option) {
            return (allele.allele_assessment.seconds_since_update / (3600 * 24)) >=
                    option.outdated_after_days;
        }
        else {
            return false;
        }
    }

    static hasExistingReferenceAssessment(allele, reference, allele_state) {
        if (this.allele.reference_assessments) {
            return this.allele.reference_assessments.find(ra => {
                return ra.reference_id === reference.id;
            });
        }
        return false;
    }

}
