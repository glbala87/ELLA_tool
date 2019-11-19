var Page = require('./page')
var util = require('./util')

const SELECTOR_COMMENT_ACMG = 'acmg.id-staged-acmg-code wysiwyg-editor.id-comment-acmg'
const SELECTOR_COMMENT_ACMG_EDITOR = `${SELECTOR_COMMENT_ACMG} .wysiwygeditor`

class AnalysisPage extends Page {
    get overviewLink() {
        return util.element('a#home-bttn')
    }

    get title() {
        return util.element('.id-workflow-instance').getText()
    }
    get analysis() {
        return util.element('analysis')
    }

    // button has many uses, where button text varies:
    get finishButton() {
        return util.element('.id-finish-analysis')
    }
    get startButton() {
        return util.element('.id-start-analysis')
    }
    get saveButton() {
        return util.element('.id-start-analysis')
    }
    get reopenButton() {
        return util.element('.id-start-analysis')
    }

    get classificationTypeFullButton() {
        return util.element('label#classification-type-full')
    }

    get classificationTypeQuickButton() {
        return util.element('label#classification-type-quick')
    }

    get classificationTypeVisualButton() {
        return util.element('label#classification-type-visual')
    }

    // acmg modal to choose code:
    get acmgComment() {
        return $(SELECTOR_COMMENT_ACMG)
    }

    // buttons in modal
    get modalFinishButton() {
        return util.element('.id-finish')
    }
    get markInterpretationButton() {
        return util.element('.id-mark-interpretation')
    }
    get markReviewButton() {
        return util.element('.id-mark-review')
    }
    get markMedicalReviewButton() {
        return util.element('.id-mark-medicalreview')
    }
    get finalizeButton() {
        return util.element('.id-finalize')
    }

    get addExcludedButton() {
        return util.element('button.id-add-excluded')
    }

    getRounds() {
        let selector = '.id-interpretationrounds-dropdown option'
        return $$(selector).map((a) => a.getText())
    }

    chooseRound(number) {
        let dropdownOption = $(`.id-interpretationrounds-dropdown option:nth-child(${number})`)
        dropdownOption.waitForExist()
        dropdownOption.click()
    }

    selectSectionClassification() {
        $('#section-classification').click()
    }

    selectSectionReport() {
        $('#section-report').click()
    }

    addAttachment() {
        let uploadSelector = '.input-label #file-input'
        const remoteFilePath = browser.uploadFile(__filename)
        browser.execute(`document.querySelector(".input-label #file-input").hidden = false`)
        const el = $(uploadSelector)
        el.setValue(remoteFilePath)
        browser.execute(`document.querySelector(".input-label #file-input").hidden = true`)
        console.log('Added attachment')
    }

    /**
     * @param {string} category Either 'pathogenic', 'benign', or 'other'
     * @param {string} code ACMG code to add
     * @param {string} comment Comment to go with added code
     * @param {int} adjust_levels Adjust ACMG code up or down level (-2 is down two times etc.)
     *
     * Choose an ACMG code high up in the modal to avoid 'element not clickable' errors
     *
     */
    addAcmgCode(category, code, comment, adjust_levels = 0) {
        const buttonSelector = 'button.id-add-acmg' // Select top sectionbox' button
        $(buttonSelector).click()
        $('.id-acmg-selection-popover').waitForExist() // make sure the popover appeared
        browser.pause(200) // Wait for popover animation to settle

        let categories = {
            pathogenic: 1,
            benign: 2,
            other: 3
        }

        let acmg_selector = `.id-acmg-selection-popover .id-acmg-category:nth-child(${categories[category]})`
        $(acmg_selector).click()
        $('.acmg-selection-popover')
            .$(`h4.acmg-title=${code}`)
            .click()

        // Set staged code comment
        this.acmgComment.click()
        $(SELECTOR_COMMENT_ACMG_EDITOR).setValue(comment)

        // Adjust staged code up or down
        let adjust_down = adjust_levels < 0
        for (let i = 0; i < Math.abs(adjust_levels); i++) {
            if (adjust_down) {
                util.element('.id-staged-acmg-code .id-adjust-down').click()
            } else {
                util.element('.id-staged-acmg-code .id-adjust-up').click()
            }
        }

        // Add staged code
        util.element('.id-staged-acmg-code .acmg-upper button').click()
        // Hide popover
        $(buttonSelector).click()
        // Wait for popover to fade out
        browser.pause(200)
    }

    getFinalizePossible() {
        $('.id-finish-analysis').waitForDisplayed()
        $('#nprogress').waitForExist(undefined, true)
        this.finishButton.click()
        this.finalizeButton.click()
        const finalizePossible = util.elementOrNull('.id-finalize-not-possible') === null
        // Close modal
        $('body').click()
        return finalizePossible
    }

    getSuggestedClass() {
        return util.element('.suggested-class').getText()
    }
}

module.exports = AnalysisPage
