var Page = require('./page')

const SELECTOR_COMMENT_ACMG = 'acmg.id-staged-acmg-code wysiwyg-editor.id-comment-acmg';
const SELECTOR_COMMENT_ACMG_EDITOR = `${SELECTOR_COMMENT_ACMG} .wysiwygeditor`;

class AnalysisPage extends Page {

    get title() { return browser.element('.id-workflow-instance').getText(); }
    get analysis() { return browser.element('analysis'); }

    // button has many uses, where button text varies:
    get finishButton() { return browser.element('.id-finish-analysis'); }
    get startButton() { return browser.element('.id-start-analysis'); }
    get saveButton() { return browser.element('.id-start-analysis'); }
    get reopenButton() { return browser.element('.id-start-analysis'); }

    // acmg modal to choose code:
    get acmgComment() { return $(SELECTOR_COMMENT_ACMG);}

    // buttons in modal
    get markReviewButton() { return browser.element('.id-mark-review'); }
    get finalizeButton() { return browser.element('.id-finalize'); }

    get addExcludedButton() { return browser.element('.id-add-excluded') }
    get collisionWarningBar() { return browser.element('.toast-message-collision'); }

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

    selectSectionClassification() {
        let classificationSelector = '#section-classification';
        browser.click(classificationSelector)
    }

    selectSectionReport() {
        let reportSelector = '#section-report';
        browser.click(reportSelector)
    }

    addAttachment() {
        let uploadSelector = '.input-label #file-input';
        // let uploadSelector = '#file-input';
        browser.chooseFile(uploadSelector, __filename)
        browser.pause(1000)
        console.log("Added attachment")
    }

    /**
     * @param {string} category Either 'pathogenic' or 'benign'
     * @param {string} code ACMG code to add
     * @param {string} comment Comment to go with added code
     * @param {int} adjust_levels Adjust ACMG code up or down level (-2 is down two times etc.)
     *
     * Choose an ACMG code high up in the modal to avoid 'element not clickable' errors
     *
     */
    addAcmgCode(category, code, comment, adjust_levels=0) {

        let buttonSelector = 'nav.bottom button.id-add-acmg'; // Select top sectionbox' button
        browser.click(buttonSelector);
        browser.waitForExist('.id-acmg-selection-popover', 100); // make sure the popover appeared
        browser.pause(500); // Wait for popover animation to settle

        let categories = {
            pathogenic: 1,
            benign: 2
        };

        let acmg_selector = `.id-acmg-selection-popover .id-acmg-category:nth-child(${categories[category]})`;
        browser.click(acmg_selector);
        browser.element('.popover').scroll(`h4.acmg-title=${code}`);
        browser.element('.popover').click(`h4.acmg-title=${code}`);

        // Set staged code comment
        this.acmgComment.click();
        browser.setValue(SELECTOR_COMMENT_ACMG_EDITOR, comment);

        // Adjust staged code up or down
        let adjust_down = adjust_levels < 0;
        for (let i = 0; i < Math.abs(adjust_levels); i++) {
            if (adjust_down) {
                browser.element('.acmg-selection .id-staged-acmg-code .id-adjust-down').click();
            } else {
                browser.element('.acmg-selection .id-staged-acmg-code .id-adjust-up').click();
            }
        }

        // Add staged code
        browser.element('.acmg-selection .id-staged-acmg-code .acmg-upper button').click();

    }

}

module.exports = AnalysisPage;
