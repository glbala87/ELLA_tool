var Page = require('./page')

class AnalysisPage extends Page {

    get analysis() { return browser.element('analysis'); }
    get finishButton() { return browser.element('.id-finish-analysis'); }
    get startButton() { return browser.element('.id-start-analysis'); }
    get markReviewButton() { return browser.element('.id-mark-review'); }
    get finalizeButton() { return browser.element('.id-finalize'); }
    get addExcludedButton() { return browser.element('.id-add-excluded') }
    get collisionWarningBar() { return browser.element('.id-collision-warning'); }

    get roundCount() {
        let selector = '.id-interpretationrounds-dropdown option'
        let all = browser.getText(selector);
        if (Array.isArray(all)) {
            return all.length;
        } else {
            return 1; // if zero an exception would be called above
        }
    }

    chooseRound(number) {
        let dropdownOption = `.id-interpretationrounds-dropdown option:nth-child(${number})`;
        browser.waitForExist(dropdownOption);
        browser.click(dropdownOption);

    }

    _selectSection(number) {
        let dropdownOption = `interpretation-singlesample nav select option:nth-child(${number})`;
        browser.waitForExist(dropdownOption);
        browser.click(dropdownOption);
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

}

module.exports = AnalysisPage
