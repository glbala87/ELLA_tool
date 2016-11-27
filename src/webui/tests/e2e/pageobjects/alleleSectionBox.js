var Page = require('./page')

class AlleleSectionBox extends Page {

    get reportComment() { return browser.element('allele-sectionbox textarea[placeholder="REPORT"]'); }
    get evaluationComment() { return browser.element('allele-sectionbox textarea[placeholder="EVALUATION"]'); }
    get frequencyComment() { return browser.element('allele-sectionbox textarea[placeholder="FREQUENCY-COMMENTS"]'); }
    get externalComment() { return browser.element('allele-sectionbox textarea[placeholder="EXTERNAL DB-COMMENTS"]'); }
    get predictionComment() { return browser.element('allele-sectionbox textarea[placeholder="PREDICTION-COMMENTS"]'); }
    get classSelection() { return browser.element('allele-sectionbox select.id-select-classification'); }
    get setClassBtn() { return browser.element('allele-sectionbox button.id-set-class'); }
    get addExternalBtn() { return browser.element('allele-sectionbox button.id-add-external'); }
    get addPredictionBtn() { return browser.element('allele-sectionbox button.id-add-prediction'); }
    get classificationAcceptedBtn() { return browser.element('allele-sectionbox .id-accept-classification checked'); }

    markAsClass1() {
       browser.click('.id-mark-class1');
    }

    markAsClass2() {
       browser.click('.id-mark-class2');
    }

    markAsTechnical() {
       browser.click('.id-mark-technical');
    }

    /**
     * @param {string} category Either 'pathogenic' or 'benign'
     * @param {string} code ACMG code to add
     * @param {string} comment Comment to go with added code
     *
     */
    addAcmgCode(category, code, comment) {
        browser.click('allele-sectionbox button.id-add-acmg');
        let categories = {
            pathogenic: 1,
            benign: 2
        };

        let acmg_selector = `.id-acmg-selection-popover .id-acmg-category:nth-child(${categories[category]})`;
        browser.pause(500); // Wait for popover animation to settle
        browser.click(acmg_selector);

        browser.element('.popover').scroll(`h4.acmg-title=${code}`);
        browser.element('.popover').click(`h4.acmg-title=${code}`);

        // Set code comment
        // Newly added element will appear last in included list..
        browser.element('allele-sectionbox allele-info-acmg-selection section.included acmg:last-child textarea').setValue(comment)

        // Close sidebar
        browser.click('allele-sectionbox button.id-add-acmg');
    }

    evaluateReference(index) {
        browser.click(`allele-info-references article:nth-child(${index}) button.id-reference-evaluate`);
    }

    getReferenceComment(index) {
        return browser.getValue(`allele-info-references article:nth-child(${index}) .id-reference-comment textarea`);
    }

    getReferenceRelevance(index) {
        return browser.getText(`allele-info-references article:nth-child(${index}) .id-reference-relevance p`)
    }

    getExternalOtherAnnotation() {
        browser.waitForExist('allele-info-external-other div.cell h5');
        return browser.getText('allele-info-external-other div.cell h5');
    }

    getExternalOtherValue() {
        return browser.getText('allele-info-external-other div.cell p');
    }

     getPredictionOtherAnnotation() {
        browser.waitForExist('allele-info-prediction-other div.cell h5');
        return browser.getText('allele-info-prediction-other div.cell h5');
    }

    getPredictionOtherValue() {
        return browser.getText('allele-info-prediction-other div.cell p');
    }

    getExistingClassificationClass() {
        return browser.getText('allele-info-vardb contentbox div div.cb-body cbbody h2');
    }

    hasExistingClassification() {return browser.isExisting('allele-info-vardb'); }

}

module.exports = AlleleSectionBox;