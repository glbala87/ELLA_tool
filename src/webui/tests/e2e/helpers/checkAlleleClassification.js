let AlleleSidebar = require('../pageobjects/alleleSidebar')
let AlleleSectionBox = require('../pageobjects/alleleSectionBox')

let alleleSidebar = new AlleleSidebar()
let alleleSectionBox = new AlleleSectionBox()


/**
 *
 * Takes in allele classification data
 * @param {any} allele_data
 */
function checkAlleleClassification(allele_data) {

    for (let [allele, data] of Object.entries(allele_data)) {

        expect(alleleSidebar.isAlleleInClassified(allele)).toBe(true);
        alleleSidebar.selectClassifiedAllele(allele);
        expect(alleleSidebar.getSelectedAlleleClassification()).toEqual(data.classification);

        if ('references' in data) {
            for (let [idx, ref_data] of Object.entries(data.references)) {
                expect(alleleSectionBox.getReferenceRelevance(idx)).toEqual(ref_data.relevance);
                expect(alleleSectionBox.getReferenceComment(idx)).toEqual(ref_data.comment);
            }
        }

        if ('evaluation' in data) {
            expect(alleleSectionBox.classificationComment).toEqual(data.evaluation);
        }
        if ('frequency' in data) {
            expect(alleleSectionBox.frequencyComment).toEqual(data.frequency);
        }
        if ('prediction' in data) {
            expect(alleleSectionBox.predictionComment).toEqual(data.prediction);
        }
        if ('external' in data) {
            expect(alleleSectionBox.externalComment).toEqual(data.external);
        }
        if ('report' in data) {
            expect(alleleSectionBox.reportComment.getValue()).toEqual(data.report);
        }
    }
}

module.exports = checkAlleleClassification;