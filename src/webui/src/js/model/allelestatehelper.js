/* jshint esnext: true */

import {deepCopy} from '../util';

export class AlleleStateHelper {

    /**
     * Helper class for working with alleleState objects
     * (alleleState objects are part of the interpretation's state,
     * describing the state for one allele).
    */

    static setupAlleleState(allele_state) {
        // If not existing, return the object from the state, or create empty one
        if (!('alleleassessment' in allele_state)) {
            allele_state.alleleassessment = {
                reuse: false,
                evaluation: {
                    prediction: {
                        comment: ''
                    },
                    classification: {
                        comment: ''
                    },
                    external: {
                        comment: ''
                    },
                    frequency: {
                        comment: ''
                    },
                    acmg: {
                        included: [],
                        suggested: []
                    }
                },
                classification: null
            };
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
        this.setupAlleleState(allele_state);
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
        this.setupAlleleState(allele_state);
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
            let existing = allele.reference_assessments.find(ra => {
                return ra.reference_id === reference.id;
            });
            return existing;
        }
    }

    static hasReferenceAssessment(allele, reference, allele_state) {
        return (this.getExistingReferenceAssessment(allele, reference) ||
                this.getStateReferenceAssessment(allele, reference, allele_state));
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
            if (!('allelereport' in allele_state)) {
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
     * Toggles class 1 on/off
     * In addition to setting 'alleleassessment.classification',
     * a property class1 is also set as a flag to indicate
     * that the toggle was set (to distinguish against setting it
     * manually to same class).
     * @param  {Object} allele_state   Allele state to modify
     * @return {Boolean}              Whether toggle is true or not
     */
    static toggleClass1(allele_state) {
        // Ignore if already set as class T or class 2
        if (allele_state.classT || allele_state.class2) {
            return;
        }
        allele_state.class1 = !Boolean(allele_state.class1);
        if (allele_state.class1) {
            allele_state.alleleassessment.classification = '1';
            return true;
        }
        else {
            delete allele_state.alleleassessment.classification;
            return false;
        }
    }

    /**
     * Toggles class 2 on/off
     * In addition to setting 'alleleassessment.classification',
     * a property class2 is also set as a flag to indicate
     * that the toggle was set (to distinguish against setting it
     * manually to same class).
     * @param  {Object} allele_state   Allele state to modify
     * @return {Boolean}              Whether toggle is true or not
     */
    static toggleClass2(allele_state) {
        // Ignore if already set as class T or class 1
        if (allele_state.classT || allele_state.class1) {
            return;
        }
        allele_state.class2 = !Boolean(allele_state.class2);
        if (allele_state.class2) {
            allele_state.alleleassessment.classification = '2';
            return true;
        }
        else {
            delete allele_state.alleleassessment.classification;
            return false;
        }
    }

    /**
     * Toggles class T on/off
     * In addition to setting 'alleleassessment.classification',
     * a property classT is also set as a flag to indicate
     * that the toggle was set (to distinguish against setting it
     * manually to same class).
     * @param  {Object} allele_state   Allele state to modify
     * @return {Boolean}              Whether toggle is true or not
     */
    static toggleTechnical(allele_state) {
        // Ignore if set as class 1 or class 2
        if (allele_state.class1 || allele_state.class2) {
            return;
        }
        allele_state.classT = !Boolean(allele_state.classT);
        if (allele_state.classT) {
            allele_state.alleleassessment.classification = 'T';
            return true;
        }
        else {
            delete allele_state.alleleassessment.classification;
            return false;
        }
    }

    /**
     * Copies any existing allele's alleleassessment into the allele_state.
     * To be used when the user want's to edit the existing assessment.
     * @param  {Allele} allele   Allele to copy alleleassessment from.
     * @param  {Object} allele_state   Allele state to modify
     */
    static copyAlleleAssessmentToState(allele, allele_state) {
        if (allele.allele_assessment && !allele_state.alleleAssessmentCopied) {
            allele_state.alleleassessment.evaluation = deepCopy(allele.allele_assessment.evaluation);
            allele_state.alleleAssessmentCopied = true;
            allele_state.presented_alleleassessment_id = allele.allele_assessment.id;
        }
    }

    /**
     * Copies any existing allele's report into the allele_state.
     * To be used when the user want's to edit the existing report.
     * @param  {Allele} allele   Allele to copy report from.
     * @param  {Object} allele_state   Allele state to modify
     */
    static copyAlleleReportToState(allele, allele_state) {
        if (allele.allele_report && !allele_state.alleleReportCopied) {
            allele_state.allelereport.evaluation = deepCopy(allele.allele_report.evaluation);
            allele_state.alleleReportCopied = true;
            allele_state.presented_allelereport_id = allele.allele_report.id;
        }
    }


    /**
     * Toggles reusing the existing classification of allele.
     * If alleleassessment is outdated, it refuse to toggle on.
     * @param  {Allele} allele   Allele to reuse alleleassessment of.
     * @param  {Object} allele_state   Allele state to modify
     * @param  {Config}  config Application config
     * @return {Boolean}              Whether toggle is true or not
     */

    static toggleReuseAlleleAssessment(allele, allele_state, config, copy_on_enable=false) {
        if (!('allele_assessment' in allele)) {
            throw Error("Cannot reuse alleleassessment from allele without existing alleleassessment");
        }
        this.setupAlleleState(allele_state);
        if (this.isAlleleAssessmentReused(allele_state)) {
            allele_state.alleleassessment.reuse = false;

            // TODO: allelereport reuse is now tied to alleleassessment reuse,
            // we might want to decouple this in case user only wants to update either of them..
            allele_state.allelereport.reuse = false;
            if ('id' in allele_state.allelereport) {
                delete allele_state.allelereport.id;
            }
            // TODO: This overwrites user's data, might want to add a warning...
            this.copyAlleleAssessmentToState(allele, allele_state);
            this.copyAlleleReportToState(allele, allele_state);

            return false;
        }
        else {
            if (copy_on_enable) {
                this.copyAlleleAssessmentToState(allele, allele_state);
                this.copyAlleleReportToState(allele, allele_state);
            }

            // Check whether existing allele assessment is outdated,
            // if so refuse to toggle on.
            if (this.isAlleleAssessmentOutdated(allele, config)) {
                return false;
            }

            if ('allele_assessment' in allele) {
                allele_state.presented_alleleassessment_id = allele.allele_assessment.id;
                allele_state.alleleassessment.reuse = true;
            }
            if ('allele_report' in allele) {
                allele_state.allelereport.id = allele.allele_report.id;
                allele_state.presented_allelereport_id = allele.allele_report.id;
                allele_state.allelereport.reuse = true;
            }


            return true;
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
