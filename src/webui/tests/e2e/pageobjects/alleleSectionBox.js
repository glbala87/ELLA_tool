var Page = require('./page')


// export const BUTTON_TEXT_REUSE_EXISTING_CLASSIFICATION = 'EXISTING REUSED';

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
    get classificationAcceptedToggleBtn() { return browser.element('allele-sectionbox .id-accept-classification'); }
    get existingClassificationButtonText() { return this.classificationAcceptedToggleBtn.getText(); }


    _setClassification(index) {
        let dropdownOption = `select.id-select-classification option:nth-child(${index})`;
        // console.log(`finding selector ${dropdownOption}`);
        browser.click(dropdownOption);
    }

    classifyAsU() {
       this._setClassification(1);
    }
    classifyAsT() {
       this._setClassification(2);
    }
    classifyAs1() {
       this._setClassification(3);
    }

    classifyAs2() {
       this._setClassification(4);
    }
    classifyAs3() {
       this._setClassification(5);
    }
    classifyAs4() {
       this._setClassification(6);
    }
    classifyAs5() {
       this._setClassification(7);
    }

    unclassify() { // go through all possible buttons that 'unclassifies':
        let selectors = [
            '.id-accept-classification',
            '.id-marked-class1',
            '.id-marked-class2',
            '.id-marked-technical'
        ];

        for (let s of selectors) {
            if (browser.isExisting(s)) {
                console.info(`Unclassified variant using using button selector ${s}`);
                browser.click(s);
                return;
            }
        }

    }

    markAsClass1() {
        browser.click('.id-mark-class1');
    }

    markAsClass2() {
       browser.click('.id-mark-class2');
    }

    markAsTechnical() {
        browser.click('.id-mark-technical');
    }

    unmarkClass1() {
        browser.click('.id-marked-class1');
    }

    unmarkClass2() {
        browser.click('.id-marked-class2');
    }

    unmarkTechnical() {
        browser.click('.id-marked-technical');
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
        return browser.getText('allele-info-vardb contentbox.vardb cbbody h2');
    }

    hasExistingClassification() {
        browser.waitForExist('allele-info-vardb');
        return browser.isExisting('allele-info-vardb contentbox.vardb');
    }

}

module.exports = AlleleSectionBox;
