let Page = require('./page');
let util = require('./util');

const SELECTOR_ACMG_INCLUDED = '.id-acmg-included';

const SELECTOR_COMMENT_CLASSIFICATION = 'allele-sectionbox .id-comment-classification';
const SELECTOR_COMMENT_CLASSIFICATION_EDITOR = `${SELECTOR_COMMENT_CLASSIFICATION} .wysiwygeditor`;
const SELECTOR_COMMENT_FREQUENCY = 'allele-sectionbox .id-comment-frequency';
const SELECTOR_COMMENT_FREQUENCY_EDITOR = `${SELECTOR_COMMENT_FREQUENCY} .wysiwygeditor`;
const SELECTOR_COMMENT_EXTERNAL = 'allele-sectionbox .id-comment-external';
const SELECTOR_COMMENT_EXTERNAL_EDITOR = `${SELECTOR_COMMENT_EXTERNAL} .wysiwygeditor`;
const SELECTOR_COMMENT_PREDICTION = 'allele-sectionbox .id-comment-prediction';
const SELECTOR_COMMENT_PREDICTION_EDITOR = `${SELECTOR_COMMENT_PREDICTION} .wysiwygeditor`;
const SELECTOR_COMMENT_REPORT = 'allele-sectionbox .id-comment-report';
const SELECTOR_COMMENT_REPORT_EDITOR = `${SELECTOR_COMMENT_REPORT} .wysiwygeditor`;

const SELECTOR_FREQ_EXAC = `allele-sectionbox contentbox[title="ExAC"]`;
const SELECTOR_FREQ_GNOMAD_EXOMES = `allele-sectionbox contentbox[title="GNOMAD_EXOMES"]`;
const SELECTOR_FREQ_GNOMAD_GENOMES = `allele-sectionbox contentbox[title="GNOMAD_GENOMES"]`;

const SELECTOR_EXISTING_CLASSIFICATION = 'allele-sectionbox contentbox.vardb .id-classification-name';
const SELECTOR_TOGGLE_ACCEPTED_CLASSIFICATION = 'allele-sectionbox .id-accept-classification';
const BUTTON_TEXT_REUSE_EXISTING_CLASSIFICATION = 'REEVALUATE';


class AlleleSectionBox  {

    get exacElement() { return browser.element(SELECTOR_FREQ_EXAC); }
    get gnomADExomesElement() { return browser.element(SELECTOR_FREQ_GNOMAD_EXOMES); }
    get gnomADGenomesElement() { return browser.element(SELECTOR_FREQ_GNOMAD_GENOMES); }

    get reviewCommentElement() { return browser.element('.workflow-options input.id-review-comment'); }

    get classificationCommentElement() { return browser.element(SELECTOR_COMMENT_CLASSIFICATION);}
    get classificationComment() { return browser.getText(SELECTOR_COMMENT_CLASSIFICATION_EDITOR); }
    get existingClassificationName() { return browser.getText(SELECTOR_EXISTING_CLASSIFICATION); }

    setClassificationComment(text) {
        this.classificationCommentElement.scroll();
        this.classificationCommentElement.click();
        browser.setValue(SELECTOR_COMMENT_CLASSIFICATION_EDITOR, text);
    }


    get frequencyCommentElement() { return browser.element(SELECTOR_COMMENT_FREQUENCY);}
    get frequencyComment() { return browser.getText(SELECTOR_COMMENT_FREQUENCY_EDITOR); }

    setFrequencyComment(text) {
        this.frequencyCommentElement.scroll();
        this.frequencyCommentElement.click();
        browser.setValue(SELECTOR_COMMENT_FREQUENCY_EDITOR, text);
    }

    get externalCommentElement() { return browser.element(SELECTOR_COMMENT_EXTERNAL);}
    get externalComment() { return browser.getText(SELECTOR_COMMENT_EXTERNAL_EDITOR); }

    setExternalComment(text) {
        this.externalCommentElement.scroll();
        this.externalCommentElement.click();
        browser.setValue(SELECTOR_COMMENT_EXTERNAL_EDITOR, text);
    }

    get predictionCommentElement() { return browser.element(SELECTOR_COMMENT_PREDICTION);}
    get predictionComment() { return browser.getText(SELECTOR_COMMENT_PREDICTION_EDITOR); }

    setPredictionComment(text) {
        this.predictionCommentElement.scroll();
        this.predictionCommentElement.click();
        browser.setValue(SELECTOR_COMMENT_PREDICTION_EDITOR, text);
    }

    get reportCommentElement() { return browser.element(SELECTOR_COMMENT_REPORT); }
    get reportComment() { return browser.getText(SELECTOR_COMMENT_REPORT_EDITOR); }
    get reportCommentEditable() { return browser.isCommentEditable(SELECTOR_COMMENT_REPORT_EDITOR)}

    setReportComment(text) {
        this.reportCommentElement.scroll();
        this.reportCommentElement.click();
        browser.setValue(SELECTOR_COMMENT_REPORT_EDITOR, text);
    }


    get classSelection() { return browser.element('allele-sectionbox select.id-select-classification'); }
    get setClassBtn() { return browser.element('allele-sectionbox button.id-set-class'); }
    get addExternalBtn() { return browser.element('allele-sectionbox button.id-add-external'); }
    get addPredictionBtn() { return browser.element('allele-sectionbox button.id-add-prediction'); }
    get addReferencesBtn() { return browser.element('allele-sectionbox button.id-add-references' ); }
    get classificationAcceptedBtn() { return browser.element('allele-sectionbox .id-accept-classification checked'); }
    get classificationAcceptedToggleBtn() {
        return util.elementOrNull(SELECTOR_TOGGLE_ACCEPTED_CLASSIFICATION);
    }

    get existingClassificationButtonText() { return this.classificationAcceptedToggleBtn.getText(); }

    reusingClassification() {
        return this.existingClassificationButtonText.toLowerCase() === BUTTON_TEXT_REUSE_EXISTING_CLASSIFICATION.toLowerCase()
    }

    _setClassification(index) {
        let dropdownOption = `select.id-select-classification option:nth-child(${index})`;
        // console.log(`finding selector ${dropdownOption}`);
        browser.click(dropdownOption);
    }

    setClassificationByText(value) {
        let option = this.classSelection.selectByVisibleText(value);
        if (!option) {
            console.error(`Didn't find classifiation option with value '${value}'`);
        }
    }

    getClassificationValue() {
        // the value of the selected option element. This is different than the label shown.
        return this.classSelection.getValue();
    }

    _getClassificationLabel() {
        return this.classSelection.getText('option:checked');
    }

    isClassU() {
        return this._getClassificationLabel().toLowerCase() === "Unclassified".toLowerCase();
    }

    isClassT() {
        return this._getClassificationLabel().toLowerCase() === "Technical".toLowerCase();
    }

    isClass1() {
        return this._getClassificationLabel().toLowerCase() === "Class 1".toLowerCase();
    }

    isClass2() {
        return this._getClassificationLabel().toLowerCase() === "Class 2".toLowerCase();
    }

    isClass3() {
        return this._getClassificationLabel().toLowerCase() === "Class 3".toLowerCase();
    }

    isClass4() {
        return this._getClassificationLabel().toLowerCase() === "Class 4".toLowerCase();
    }

    isClass5() {
        return this._getClassificationLabel().toLowerCase() === "Class 5".toLowerCase();
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

    getNumberOfAttachments() {
        let elements = browser.elements('.attachment-wrapper attachment')
        return elements.value.length;
    }

    evaluateReference(index) {
        let referenceSelector = `allele-info-published-references article:nth-child(${index})`;
        let title = browser.getText(`${referenceSelector} .id-reference-title`);
        browser.click(`${referenceSelector} button.id-reference-evaluate`);
        return title;
    }

    getReferenceComment(index) {
        const selector = `allele-info-published-references article:nth-child(${index}) .id-reference-comment .wysiwygeditor`;
        return browser.getText(selector);
    }

    getReferenceRelevance(index) {
        return browser.getText(`allele-info-published-references article:nth-child(${index}) .id-reference-relevance p`)
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

    expandSectionClassification() {
        let sectionSelector = 'allele-sectionbox .id-sectionbox-classification section';
        let comment = browser.selectorExecute('allele-sectionbox .id-sectionbox-classification section',
            function(matchingElements) {
                return matchingElements[0].className = matchingElements[0].className.replace("collapsed", "");
        });
        util.log(`CSS class of ${sectionSelector} is now ${comment}`);
    }

    getReferences() {
        return browser.elements('allele-sectionbox .id-references-box article');
    }
}

module.exports = AlleleSectionBox;
