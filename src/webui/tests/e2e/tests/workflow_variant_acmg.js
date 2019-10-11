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
let failFast = require('jasmine-fail-fast')

let loginPage = new LoginPage()
let variantSelectionPage = new VariantSelectionPage()
let analysisPage = new AnalysisPage()
let alleleSectionBox = new AlleleSectionBox()

jasmine.getEnv().addReporter(failFast.init())

describe(`ACMG`, function() {
    beforeAll(() => {
        browser.resetDb()
    })

    function expectSuggestedFeatureIsHidden() {
        expect(acmg.suggestedElement.isVisible()).toBe(false)
        expect(acmg.showHideBtn.isVisible()).toBe(false)
    }

    function expectSuggestedFeatureIsShown() {
        expect(acmg.suggestedElement.isVisible()).toBe(true)
        expect(acmg.showHideBtn.isVisible()).toBe(true)
    }

    it('suggested codes and REQs are displayed when interpreting', function() {
        loginPage.open()
        loginPage.selectFirstUser()
        variantSelectionPage.selectPending(5)
        analysisPage.startButton.click()
        alleleSectionBox.classifyAs1()
        expectSuggestedFeatureIsShown()

        analysisPage.finishButton.click()
        analysisPage.finalizeButton.click()
        analysisPage.modalFinishButton.click()
    })

    describe('suggested codes and REQs are', function() {
        beforeAll(function() {
            // classify one variant as 'U'
            loginPage.open()
            loginPage.selectFirstUser()
            variantSelectionPage.selectPending(1)
            analysisPage.startButton.click()
            alleleSectionBox.classifyAsU()
            analysisPage.finishButton.click()
            analysisPage.finalizeButton.click()
            analysisPage.modalFinishButton.click()

            // select the first we finished, class 1
            loginPage.open()
            loginPage.selectSecondUser()
            variantSelectionPage.expandFinishedSection()
            variantSelectionPage.selectFinished(2)
            expect(alleleSectionBox.isClass1()).toBe(true)
        })

        it('hidden when seeing a finished interpretation', function() {
            // browser.debug();
            // expect(acmg.collapsed).toBe(true);
            expect(alleleSectionBox.classificationAcceptedToggleBtn).toBeDefined()
            expectSuggestedFeatureIsHidden()
        })

        it('are shown after opening a finished interpretation', function() {
            // reopen the interpretation
            analysisPage.startButton.click()
            expect(alleleSectionBox.classificationAcceptedToggleBtn).toBeDefined()
            expectSuggestedFeatureIsShown()
        })

        it('are shown after starting a finished interpretation', function() {
            // start the interpreation
            expect(alleleSectionBox.classificationAcceptedToggleBtn).toBeDefined()
            expect(alleleSectionBox.reusingClassification()).toBe(true)
            analysisPage.startButton.click()

            expectSuggestedFeatureIsShown()
        })

        it('are shown when a reclassification is started', function() {
            // start (re) classification
            alleleSectionBox.classificationAcceptedToggleBtn.click()

            expect(alleleSectionBox.reusingClassification()).toBe(false)
            expectSuggestedFeatureIsShown()

            // let's reuse the existing classification
            alleleSectionBox.classificationAcceptedToggleBtn.click()

            expectSuggestedFeatureIsShown()

            analysisPage.finishButton.click()
            analysisPage.finalizeButton.click()
            analysisPage.modalFinishButton.click()
        })
    })
})
