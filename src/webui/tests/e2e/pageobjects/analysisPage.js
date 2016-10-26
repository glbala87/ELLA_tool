var Page = require('./page')

class AnalysisPage extends Page {

    get analysis() { return browser.element('analysis'); }
    get finishButton() { return browser.element('.id-finish-analysis-btn'); }
    get startButton() { return browser.element('.id-start-analysis-btn'); }
    get markReviewButton() { return browser.element('.id-mark-review-btn'); }
    get finalizeButton() { return browser.element('.id-finalize-btn'); }

    _selectSection(number) {
        let dropdown = `interpretation-singlesample nav select option:nth-child(${number})`;
        browser.waitForExists(dropdown);
        browser.click(dropdown);
    }

    selectSectionFrequency() {
       this._selectSection(1);
    }

    selectSectionClassification() {
       this._selectSection(2);
    }

    selectSectionReport() {
       this._selectSection(3);
    }

    startAnalysis() {

    }

}

module.exports = AnalysisPage
