require('core-js/fn/object/entries');
require('repl');

/**
 * Displaying ACMG codes
 */

let LoginPage = require('../pageobjects/loginPage');
let VariantSelectionPage = require('../pageobjects/overview_variants');
let AnalysisPage = require('../pageobjects/analysisPage');
let AlleleSectionBox = require('../pageobjects/alleleSectionBox');
let ACMG = require('../pageobjects/acmg');
let failFast = require('jasmine-fail-fast');

let loginPage = new LoginPage();
let variantSelectionPage = new VariantSelectionPage();
let analysisPage = new AnalysisPage();
let alleleSectionBox = new AlleleSectionBox();
let acmg = new ACMG();

jasmine.getEnv().addReporter(failFast.init());

const OUR_VARIANT =  'c.581G>A';
var x = 4;
console.log('erik')
describe(`ACMG`, function () {
repl
    repl(function(code) {return eval(code)}.bind(this), require);

    beforeAll(() => {
        browser.resetDb();
    });

    it('suggested codes are displayed', function () {
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


    it('suggested codes are hidden when reusing existing classification', function () {
        loginPage.selectSecondUser();
        variantSelectionPage.expandFinishedSection();
        variantSelectionPage.selectTopFinished();

        browser.debug();
        expect(alleleSectionBox.reusingClassification()).toBe(true);
        expect(acmg.suggestedElement).toBeUndefined("Suggested should be hidden");
        expect(acmg.suggestedReqElement).toBeUndefined("Suggested REQ should be hidden");
        expect(acmg.hasShowHideButton()).toBe(false, "Button should be hidden");

        analysisPage.startButton.click();

        expect(acmg.suggestedElement).toBeUndefined();
        expect(acmg.suggestedReqElement).toBeUndefined();
        expect(acmg.hasShowHideButton()).toBe(false);


        alleleSectionBox.classificationAcceptedToggleBtn.click();

        expect(acmg.suggestedElement).toBeDefined();
        expect(acmg.suggestedReqElement).toBeDefined();
        expect(acmg.hasShowHideButton()).toBe(true);

        alleleSectionBox.classificationAcceptedToggleBtn.click();

        expect(acmg.suggestedElement).toBeUndefined();
        expect(acmg.suggestedReqElement).toBeUndefined();
        expect(acmg.hasShowHideButton()).toBe(false);

        analysisPage.finishButton.click();
        analysisPage.finalizeButton.click();
    });

});
