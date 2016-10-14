var Page = require('./page')

class AlleleSectionBox extends Page {

    get reportComment() { return browser.element('allele-sectionbox textarea[placeholder="REPORT"]'); }
    get evaluationComment() { return browser.element('allele-sectionbox textarea[placeholder="EVALUATION"]'); }
    get frequencyComment() { return browser.element('allele-sectionbox textarea[placeholder="FREQUENCY-COMMENTS"]'); }
    get externalComment() { return browser.element('allele-sectionbox textarea[placeholder="EXTERNAL DB-COMMENTS"]'); }
    get predictionComment() { return browser.element('allele-sectionbox textarea[placeholder="PREDICTION-COMMENTS"]'); }
    get classSelection() { return browser.element('allele-sectionbox select.id-select-classification'); }
    get setClassBtn() { return browser.element('allele-sectionbox button.id-set-class'); }

    markAsClass1() {
       browser.click('.id-mark-class1');
    }

    markAsClass2() {
       browser.click('.id-mark-class2');
    }

    markAsTechnical() {
       browser.click('.id-mark-technical');
    }

    markAsTechnical() {
       browser.click('.id-mark-technical');
    }


}

module.exports = AlleleSectionBox