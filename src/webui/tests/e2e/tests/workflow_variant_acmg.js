require('core-js/fn/object/entries')

/**
 * Displaying ACMG codes when interpreting.
 *
 * In some we don't want Suggested codes/Reqs to be shown. This could be implemented by some sort of hiding
 * (setting to size zero, opacity 0 etc, display:none) or by not putting them in the DOM. The implementation will
 * influence how the tests/page objects are designed.
 */

let LoginPage = require('../pageobjects/loginPage')
let VariantSelectionPage = require('../pageobjects/overview_variants')
let AnalysisPage = require('../pageobjects/analysisPage')
let AlleleSectionBox = require('../pageobjects/alleleSectionBox')
let acmg = require('../pageobjects/acmg')

let loginPage = new LoginPage()
let variantSelectionPage = new VariantSelectionPage()
let analysisPage = new AnalysisPage()
let alleleSectionBox = new AlleleSectionBox()

describe(`ACMG`, function() {
    beforeAll(() => {
        browser.resetDb()
    })

    function expectSuggestedFeatureIsHidden() {
        expect(acmg.suggestedElement.isDisplayed()).toBe(false)
        expect(acmg.showHideBtn.isDisplayed()).toBe(false)
    }

    function expectSuggestedFeatureIsShown() {
        expect(acmg.suggestedElement.isDisplayed()).toBe(true)
        expect(acmg.showHideBtn.isDisplayed()).toBe(true)
    }

    it('suggested codes and REQs are displayed when interpreting', function() {
        loginPage.open()
        loginPage.loginAs('testuser1')
        variantSelectionPage.selectPending(5)
        analysisPage.startButton.click()
        alleleSectionBox.classifyAs1()
        expectSuggestedFeatureIsShown()
        alleleSectionBox.finalize()
        analysisPage.finishButton.click()
        analysisPage.finalizeButton.click()
        analysisPage.modalFinishButton.click()
    })

    describe('suggested codes and REQs are', function() {
        beforeAll(function() {
            // classify one variant as 'U'
            loginPage.open()
            loginPage.loginAs('testuser1')
            variantSelectionPage.selectPending(1)
            analysisPage.startButton.click()
            alleleSectionBox.classifyAsU()
            alleleSectionBox.finalize()
            analysisPage.finishButton.click()
            analysisPage.finalizeButton.click()
            analysisPage.modalFinishButton.click()

            // select the first we finished, class 1
            loginPage.open()
            loginPage.loginAs('testuser2')
            variantSelectionPage.expandFinishedSection()
            variantSelectionPage.selectFinished(2)
            expect(alleleSectionBox.isClass1()).toBe(true)
        })

        it('hidden when seeing a finished interpretation', function() {
            expect(alleleSectionBox.reevaluateBtn.isDisplayed()).toBe(true)
            expectSuggestedFeatureIsHidden()
        })

        it('are shown after opening a finished interpretation', function() {
            // reopen the interpretation
            analysisPage.startButton.click()
            expect(alleleSectionBox.reevaluateBtn.isDisplayed()).toBe(true)
            expectSuggestedFeatureIsShown()
        })

        it('are shown after starting a finished interpretation', function() {
            // start the interpreation
            expect(alleleSectionBox.reevaluateBtn.isDisplayed()).toBe(true)
            analysisPage.startButton.click()
            expectSuggestedFeatureIsShown()
        })

        it('are shown when a reclassification is started', function() {
            // start (re) classification
            alleleSectionBox.reevaluateBtn.click()

            expect(alleleSectionBox.undoRevaluationBtn.isDisplayed()).toBe(true)
            expectSuggestedFeatureIsShown()

            // let's reuse the existing classification
            alleleSectionBox.undoReevaluation()

            expectSuggestedFeatureIsShown()

            analysisPage.finishButton.click()
            analysisPage.finalizeButton.click()
            analysisPage.modalFinishButton.click()
        })
    })
})
