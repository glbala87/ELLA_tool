require('core-js/fn/object/entries');

/**
 * Displaying ACMG codes
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


    it('suggested codes and REQs are hidden when reusing existing classification', function () {
        loginPage.selectSecondUser();
        variantSelectionPage.expandFinishedSection();
        variantSelectionPage.selectTopFinished();

        analysisPage.startButton.click(); // reopen

        analysisPage.startButton.click(); // start review
        expect(alleleSectionBox.reusingClassification()).toBe(true);
        expect(acmg.suggestedElement).toBeNull();
        expect(acmg.suggestedReqElement).toBeNull();
        expect(acmg.hasShowHideButton()).toBe(false);

        alleleSectionBox.classificationAcceptedToggleBtn.click();

        expect(acmg.suggestedElement).toBeDefined();
        expect(acmg.suggestedReqElement).toBeDefined();
        expect(acmg.hasShowHideButton()).toBe(true);

        alleleSectionBox.classificationAcceptedToggleBtn.click();

        expect(acmg.suggestedElement).toBeNull();
        expect(acmg.suggestedReqElement).toBeNull();
        expect(acmg.hasShowHideButton()).toBe(false);

        analysisPage.finishButton.click();
        analysisPage.finalizeButton.click();
    });

});
