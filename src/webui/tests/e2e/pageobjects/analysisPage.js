var Page = require('./page')

class AnalysisPage extends Page {

    get title() { return browser.element('.id-workflow-instance').getText(); }
    get analysis() { return browser.element('analysis'); }

    // button has many uses, where button text varies:
    get finishButton() { return browser.element('.id-finish-analysis'); }
    get startButton() { return browser.element('.id-start-analysis'); }
    get saveButton() { return browser.element('.id-start-analysis'); }
    get reopenButton() { return browser.element('.id-start-analysis'); }

    // buttons in modal
    get markReviewButton() { return browser.element('.id-mark-review'); }
    get finalizeButton() { return browser.element('.id-finalize'); }

    get addExcludedButton() { return browser.element('.id-add-excluded') }
    get collisionWarningBar() { return browser.element('.id-collision-warning'); }

    get roundCount() {
        let selector = '.id-interpretationrounds-dropdown option';
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
        let dropdownOption = `workflow-analysis nav select option:nth-child(${number})`;
        // console.log(`finding selector ${dropdownOption}`);
        browser.waitForExist(dropdownOption);
        browser.click(dropdownOption);
    }

    selectSectionClassification() {
       this._selectSection(1);
    }

    selectSectionReport() {
       this._selectSection(2);
    }

}

module.exports = AnalysisPage;
