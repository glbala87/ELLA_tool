/* jshint esnext: true */

export class AlleleStateHelper {

    /**
     * Helper class for working with alleleState objects
     * (alleleState objects are part of the interpretation's state,
     * describing the state for one allele).
    */

    static setupAlleleAssessment(allele, allele_state) {
        // If not existing, return the object from the state, or create empty one
        if (!('alleleassessment' in allele_state)) {
            allele_state.alleleassessment = {
                evaluation: {},
                classification: null,
            };
        }

        if (!('referenceassessments' in allele_state)) {
            allele_state.referenceassessments = [];
        }

        // Check if we've copied before, if so, don't overwrite on setup
        // in case user has entered something in the meantime
        if (!('alleleAssessmentCopied' in allele_state) ||
            !allele_state.alleleAssessmentCopied) {
            this.copyAlleleAssessmentToState(allele, allele_state);
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
        if (this.isAlleleAssessmentReused(allele_state)) {
            if (!('allele_assessment' in allele)) {
                throw Error("Alleleassessment set as reused, but there's no allele_assessment in provided allele.");
            }
            return allele.allele_assessment.classification;
        }
        else if ('classification' in allele_state.alleleassessment) {
                return allele_state.alleleassessment.classification;
        }
        else {
            return null;
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
     * Toggles class 2 on/off
     * In addition to setting 'alleleassessment.classification',
     * a property class2 is also set as a flag to indicate
     * that the toggle was set (to distinguish against setting it
     * manually to same class).
     * @param  {Object} allele_state   Allele state to modify
     * @return {Boolean}              Whether toggle is true or not
     */
    static toggleClass2(allele_state) {
        // Ignore if already set as class T
        if (allele_state.classT) {
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
        // Ignore if set as class 2
        if (allele_state.class2) {
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
     * @param  {Allele} allele   Allele to copy alleleassessment from.
     * @param  {Object} allele_state   Allele state to modify
     */
    static copyAlleleAssessmentToState(allele, allele_state) {
        if (allele.allele_assessment) {
            // We need to "deepcopy" to avoid overwriting
            // JS needs a deep clone function :-(
            allele_state.alleleassessment.evaluation = JSON.parse(JSON.stringify(allele.allele_assessment.evaluation));
            allele_state.alleleAssessmentCopied = true;
        }
    }

    /**
     * Toggles reusing the existing classification of allele
     * @param  {Allele} allele   Allele to reuse alleleassessment of.
     * @param  {Object} allele_state   Allele state to modify
     * @return {Boolean}              Whether toggle is true or not
     */

    static toggleReuseAlleleAssessment(allele, allele_state) {
        if (!('allele_assessment' in allele)) {
            throw Error("Cannot reuse alleleassessment from allele without existing alleleassessment");
        }
        if ('id' in allele_state.alleleassessment) {
            delete allele_state.alleleassessment.id;
            return false;
        }
        else {
            if ('allele_assessment' in allele) {
                allele_state.alleleassessment.id = allele.allele_assessment.id;
            }
            this.copyAlleleAssessmentToState(allele, allele_state);
            return true;
        }
    }

    static isAlleleAssessmentReused(allele_state) {
        return 'alleleassessment' in allele_state &&
               'id' in allele_state.alleleassessment;
    }

}
