var Page = require('./page');


// export const BUTTON_TEXT_REUSE_EXISTING_CLASSIFICATION = 'EXISTING REUSED';

const SECTION_EXPAND_SELECTOR  = " header .sb-title-container";

const SELECTOR_COMMENT_CLASSIFICATION = 'allele-sectionbox .id-comment-classification';
const SELECTOR_COMMENT_CLASSIFICATION_EDITOR = `${SELECTOR_COMMENT_CLASSIFICATION} .wysiwygeditor`;
const SELECTOR_COMMENT_FREQUENCY = 'allele-sectionbox .id-comment-frequency';
const SELECTOR_COMMENT_FREQUENCY_EDITOR = `${SELECTOR_COMMENT_FREQUENCY} .wysiwygeditor`;
const SELECTOR_COMMENT_EXTERNAL = 'allele-sectionbox .id-comment-external';
const SELECTOR_COMMENT_EXTERNAL_EDITOR = `${SELECTOR_COMMENT_EXTERNAL} .wysiwygeditor`;
const SELECTOR_COMMENT_PREDICTION = 'allele-sectionbox .id-comment-prediction';
const SELECTOR_COMMENT_PREDICTION_EDITOR = `${SELECTOR_COMMENT_PREDICTION} .wysiwygeditor`;

class AlleleSectionBox extends Page {

    get classificationCommentElement() { return browser.element(SELECTOR_COMMENT_CLASSIFICATION);}
    get classificationComment() { return browser.getText(SELECTOR_COMMENT_CLASSIFICATION_EDITOR); }

    setClassificationComment(text) {
        this.classificationCommentElement.click();
        // this.classificationCommentElement.click().waitForVisible('.wysiwygeditor', 50).setValue('.wysiwygeditor', text);
        browser.setValue(SELECTOR_COMMENT_CLASSIFICATION_EDITOR, text);
    }


    get frequencyCommentElement() { return browser.element(SELECTOR_COMMENT_FREQUENCY);}
    get frequencyComment() { return browser.getText(SELECTOR_COMMENT_FREQUENCY_EDITOR); }

    setFrequencyComment(text) {
        this.frequencyCommentElement.click();
        browser.setValue(SELECTOR_COMMENT_FREQUENCY_EDITOR, text);
    }

    get externalCommentElement() { return browser.element(SELECTOR_COMMENT_EXTERNAL);}
    get externalComment() { return browser.getText(SELECTOR_COMMENT_EXTERNAL_EDITOR); }

    setExternalComment(text) {
        this.externalCommentElement.click();
        browser.setValue(SELECTOR_COMMENT_EXTERNAL_EDITOR, text);
    }

    get predictionCommentElement() { return browser.element(SELECTOR_COMMENT_PREDICTION);}
    get predictionComment() { return browser.getText(SELECTOR_COMMENT_PREDICTION_EDITOR); }

    setPredictionComment(text) {
        this.predictionCommentElement.click();
        browser.setValue(SELECTOR_COMMENT_PREDICTION_EDITOR, text);
    }

    // get reportComment() {
    //         let element = browser.element('allele-sectionbox .id-comment-evaluation .wysiwygeditor');
    //     return element.getText();
    // }
    get reportComment() { return browser.element('allele-sectionbox textarea[placeholder="REPORT"]'); }

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
     * Choose an ACMG code high up in the modal to avoid 'element not clickable' errors
     *
     */
    addAcmgCode(category, code, comment) {

        let buttonSelector = 'allele-sectionbox button.id-add-acmg';
        browser.click(buttonSelector);
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
        browser.click(buttonSelector);
    }

    evaluateReference(index) {
        let referenceSelector = `allele-info-references article:nth-child(${index})`;
        let title = browser.getText(`${referenceSelector} .id-reference-title`);
        browser.click(`${referenceSelector} button.id-reference-evaluate`);
        return title;
    }

    getReferenceComment(index) {
        const selector = `allele-info-references article:nth-child(${index}) .id-reference-comment .wysiwygeditor`;
        return browser.getText(selector);
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

    expandSectionClassification() {
        let sectionSelector = 'allele-sectionbox .id-sectionbox-classification section';
        let comment = browser.selectorExecute('allele-sectionbox .id-sectionbox-classification section',
            function(matchingElements) {
                return matchingElements[0].className = matchingElements[0].className.replace("collapsed", "");
        });
        console.log(`CSS class of ${sectionSelector} is now ${comment}`);
    }

}

module.exports = AlleleSectionBox;
