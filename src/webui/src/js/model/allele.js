/* jshint esnext: true */

import {Annotation} from './annotation';

export class Allele {
    /**
     * Represents one Allele (aka variant)
     * Properties are copied from incoming data (from server),
     * but some fields are reserved internal usage, like
     * 'existingAlleleAssessment' and 'references'.
     * @param  {object} Allele data from server.
     */
    constructor(data) {
        Object.assign(this, data);
        this.references = {};
        this.existingAlleleAssessment = null;
        this._createAnnotations();
    }

    _createAnnotations() {
        // Convert pure annotation data to model object
        this.annotation = new Annotation(this.annotation);
    }

    getPubmedIds() {
        let ids = [];
        for (let ref of this.annotation.annotations.references) {
            ids.push(ref.pubmedID);
        }
        return ids;
    }

    /**
     * Populates the internal 'references' list with input.
     * Structure will look like:
     * this.references = {
     *     123: {
     *         reference: ref_obj_id_123
     *     },
     *     145: {
     *         reference: ref_obj_id_145
     *     }
     * }
     * @param {Array} references List of Reference objects
     */
    setReferences(references) {
        this.references = {};
        for (let reference of references) {
            if (reference.id in this.references) {
                this.references[reference.id].reference = reference;
            }
            else {
                this.references[reference.id] = {reference};
            }
        }
    }

    /**
     * Populates the internal 'references' list with input.
     * Note: The reference(s) for which the input refers to must have been added already
     * (see setReferences()).
     * Structure will look like:
     * this.references = {
     *     123: {
     *         reference: ref_obj_id_123,
     *         existingReferenceAssessment: ra_obj
     *     },
     *     ...
     * }
     * @param {Array} referenceassessments List of Reference objects
     */
    setReferenceAssessments(referenceassessments) {
        for (let ra of referenceassessments) {
            if (!(ra.reference_id in this.references)) {
                throw new Error("Trying to add ReferenceAssessment to Allele, but reference id doesn't exist.");
            }
            this.references[ra.reference_id].existingReferenceAssessment = ra;
        }
    }

    setAlleleAssessment(alleleassessment) {
        this.existingAlleleAssessment = alleleassessment;
    }
}
