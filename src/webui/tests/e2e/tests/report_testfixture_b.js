require('core-js/fn/object/entries');

// classifies all variants in an analysis


let LoginPage = require('../pageobjects/loginPage')
let SampleSelectionPage = require('../pageobjects/overview_samples')
let AnalysisPage = require('../pageobjects/analysisPage')
let AlleleSidebar = require('../pageobjects/alleleSidebar')
let AlleleSectionBox = require('../pageobjects/alleleSectionBox')
let failFast = require('jasmine-fail-fast');

let loginPage = new LoginPage()
let sampleSelectionPage = new SampleSelectionPage()
let analysisPage = new AnalysisPage()
let alleleSidebar = new AlleleSidebar()
let alleleSectionBox = new AlleleSectionBox()

jasmine.getEnv().addReporter(failFast.init());

const SAMPLE_NAME = 'brca_e2e_test02.HBOCUTV_v01';

describe('Sample workflow to test Sanger export', function () {

    it('classify the remall variants in second analysis', function () {
        loginPage.selectSecondUser();
        sampleSelectionPage.selectTopPending();
        expect(analysisPage.title).toBe(SAMPLE_NAME);

        analysisPage.startButton.click();

        expect(alleleSidebar.getClassifiedAlleles().length)
            .toEqual(3, `Wrong number of already classified variants for ${SAMPLE_NAME}`);

        for (let idx = 1; idx <= 2; idx++) {
            alleleSidebar.selectFirstUnclassified();
            selected_allele = alleleSidebar.getSelectedAllele();
            let comment = `REPORT_COMMENT &~øæå ${idx}`;
            alleleSectionBox.setReportComment(comment);
            console.log(`Classifying variant ${selected_allele} as class ${idx} with report '${comment}'`);
            alleleSectionBox.classSelection.selectByVisibleText(`Class ${idx}`);
            expect(alleleSidebar.isAlleleInClassified(selected_allele)).toBe(true);
        }

        expect(alleleSidebar.getClassifiedAlleles().length)
            .toEqual(5, `Wrong number of variants for ${SAMPLE_NAME} before finish`);

        analysisPage.finishButton.click();
        analysisPage.finalizeButton.click();
    });
});
