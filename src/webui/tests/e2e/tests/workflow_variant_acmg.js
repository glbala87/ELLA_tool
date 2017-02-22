require('core-js/fn/object/entries');

/**
 * Displaying ACMG codes when interpreting
 */

let LoginPage = require('../pageobjects/loginPage');
let VariantSelectionPage = require('../pageobjects/overview_variants');
let AnalysisPage = require('../pageobjects/analysisPage');
let AlleleSectionBox = require('../pageobjects/alleleSectionBox');
let acmg = require('../pageobjects/acmg');
let failFast = require('jasmine-fail-fast');

let loginPage = new LoginPage();
let variantSelectionPage = new VariantSelectionPage();
let analysisPage = new AnalysisPage();
let alleleSectionBox = new AlleleSectionBox();

jasmine.getEnv().addReporter(failFast.init());

describe(`ACMG`, function () {

    beforeAll(() => {
        browser.resetDb();
    });


    it('suggested codes and REQs are displayed when interpreting', function () {
        loginPage.selectFirstUser();
        variantSelectionPage.selectPending(5);
        analysisPage.startButton.click(); 

        alleleSectionBox.markAsTechnical();
        expect(acmg.suggestedElement).toBeDefined();
        expect(acmg.suggestedReqElement).toBeDefined();
        expect(acmg.hasShowHideButton()).toBe(true);

        analysisPage.finishButton.click();
        analysisPage.finalizeButton.click();
    });

    describe('suggested coded and REQs are', function () {

        beforeAll(function () {
            loginPage.selectSecondUser();
            variantSelectionPage.expandFinishedSection();
            variantSelectionPage.selectTopFinished();
        });

        it('hidden when seeing a finished interpretation', function () {
            expect(alleleSectionBox.classificationAcceptedToggleBtn).toBe(null);
            expect(acmg.suggestedElement).toBeNull();
            expect(acmg.suggestedReqElement).toBeNull();
            expect(acmg.hasShowHideButton()).toBe(false);

        });

        it('are hidden after opening a finished interpretation', function () {
            // reopen the interpretation
            analysisPage.startButton.click();
            expect(alleleSectionBox.classificationAcceptedToggleBtn).toBe(null);
            expect(acmg.suggestedElement).toBeNull();
            expect(acmg.suggestedReqElement).toBeNull();
            expect(acmg.hasShowHideButton()).toBe(false);
        });

        it('are hidden after starting a finished interpretation', function () {
            // start the interpreation
            analysisPage.startButton.click();
            expect(alleleSectionBox.classificationAcceptedToggleBtn).toBeDefined();
            expect(alleleSectionBox.reusingClassification()).toBe(true);
            expect(acmg.suggestedElement).toBeNull();
            expect(acmg.suggestedReqElement).toBeNull();
            expect(acmg.hasShowHideButton()).toBe(false);
        });

        it('are shown when a reclassification is started', function () {
            // start (re) classification
            alleleSectionBox.classificationAcceptedToggleBtn.click();

            expect(alleleSectionBox.reusingClassification()).toBe(false);
            expect(acmg.suggestedElement).toBeDefined();
            expect(acmg.suggestedReqElement).toBeDefined();
            expect(acmg.hasShowHideButton()).toBe(true);

            // let's reuse the existing classification
            alleleSectionBox.classificationAcceptedToggleBtn.click();

            expect(acmg.suggestedElement).toBeNull();
            expect(acmg.suggestedReqElement).toBeNull();
            expect(acmg.hasShowHideButton()).toBe(false);

            analysisPage.finishButton.click();
            analysisPage.finalizeButton.click();
        });

    });


});
