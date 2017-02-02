require('core-js/fn/object/entries');

/**
 * Finalize two analyses, checking the interpretation rounds for the finished analyses:
 * 1. Sample 1, all classified as 1, set to review,
 * 2. Sample 1, , all classified as 2, finalization
 * 3. Sample 2: alleles overlap with previous sample 1, all classified as T, finalize
 * 4. Open sample 1 (with two rounds). Check the rounds are different
 * 5. Open sample 2 (with one round). Check that some variants had an existing classification
 */

let LoginPage = require('../pageobjects/loginPage')
let SampleSelection = require('../pageobjects/overview_samples')
let AnalysisPage = require('../pageobjects/analysisPage')
let AlleleSidebar = require('../pageobjects/alleleSidebar')
let AlleleSectionBox = require('../pageobjects/alleleSectionBox')
let checkAlleleClassification = require('../helpers/checkAlleleClassification')
let failFast = require('jasmine-fail-fast');

let loginPage = new LoginPage()
let overview = new SampleSelection()
let analysisPage = new AnalysisPage()
let alleleSidebar = new AlleleSidebar()
let alleleSectionBox = new AlleleSectionBox()
const BUTTON_TEXT_REUSE_EXISTING_CLASSIFICATION = 'EXISTING REUSED';

jasmine.getEnv().addReporter(failFast.init());

describe('Sample workflow', function () {

    beforeAll(() => {
        browser.resetDb();
    });

    it('classifies variants and sets to review', function () {
        // brca_e2e_test01.HBOCUTV_v01
        loginPage.selectFirstUser();
        overview.open();
        overview.selectWithMissingAssessments(1);
        analysisPage.startButton.click();

        const numberOfUnclassified = alleleSidebar.countOfUnclassified();

        // Classify all as 1:
        for (let i=1; i<=numberOfUnclassified; i++) {
            alleleSidebar.selectFirstUnclassified();
            let selected_allele = alleleSidebar.getSelectedAllele();
            alleleSectionBox.markAsClass1();
            expect(alleleSidebar.isAlleleInClassified(selected_allele)).toBe(true);
        }

        analysisPage.finishButton.click();
        analysisPage.markReviewButton.click();
    });

    it('can change classfications from previous round and finalize', function () {
        // brca_e2e_test01.HBOCUTV_v01
        loginPage.selectSecondUser();
        overview.open();
        overview.selectTopReview();
        analysisPage.startButton.click();
        const numberOfClassifiedBefore = alleleSidebar.countOfClassified();
        expect(numberOfClassifiedBefore).toBeGreaterThan(0);
        expect(alleleSidebar.countOfUnclassified()).toBe(0);

        analysisPage.selectSectionClassification();

        // All have Class 1 from previous round, now set to Class 2:
        for (let i=1; i<=numberOfClassifiedBefore; i++) {
            let allele_element = alleleSidebar.selectClassifiedAlleleByIdx(i);
            let selected_allele = alleleSidebar.getSelectedAllele();
            expect(alleleSidebar.getSelectedAlleleClassification()).toBe('1');
            alleleSectionBox.classifyAs2()
            expect(alleleSidebar.isAlleleInClassified(selected_allele)).toBe(true);
        }

        // expect all to be (still) classified
        expect(alleleSidebar.countOfUnclassified()).toBe(0);
        expect(alleleSidebar.countOfClassified()).toBe(numberOfClassifiedBefore);

        analysisPage.finishButton.click();
        analysisPage.finalizeButton.click();

    });

    it('shows existing classifications and finalize', function () {
        //  start a second analysis
        // brca_e2e_test02.HBOCUTV_v01
        loginPage.selectThirdUser();
        overview.open();
        overview.selectWithMissingAssessments(1); // some variants assessed in another analysis
        analysisPage.startButton.click();

        const numberOfUnclassifiedBefore = alleleSidebar.countOfUnclassified();
        const numberOfClassifiedBefore = alleleSidebar.countOfClassified();
        console.log(`2nd analysis, number of classified=${numberOfClassifiedBefore}`);
        console.log(`2nd analysis, number of unlassified=${numberOfUnclassifiedBefore}`);
        expect(numberOfClassifiedBefore).toBeGreaterThan(0);

        analysisPage.selectSectionClassification();

        // first classified allele have an existing classification:
        alleleSidebar.selectFirstClassified();
        alleleSectionBox.hasExistingClassification();
        expect(alleleSectionBox.getExistingClassificationClass()).toContain('Class 2');

        // Classify all as T:
        for (let i=1; i<=numberOfClassifiedBefore; i++) {
            alleleSidebar.selectFirstClassified(); // who's first changes when unclassify/classify
            let selected_allele = alleleSidebar.getSelectedAllele();
            expect(alleleSectionBox.existingClassificationButtonText.toLowerCase()).
                toBe(BUTTON_TEXT_REUSE_EXISTING_CLASSIFICATION.toLowerCase(), 'Allele should be marked as reusing existing classification');
            alleleSectionBox.classificationAcceptedBtn.click();
            alleleSectionBox.classifyAsT();
            let classification = alleleSidebar.getSelectedAlleleClassification();
            expect(classification).toBe('T', 'Previous classification should now be T');
            expect(alleleSidebar.isAlleleInClassified(selected_allele)).toBe(true);
        }

        for (let i=1; i<=numberOfUnclassifiedBefore; i++) {
            alleleSidebar.selectFirstUnclassified(); // who's first changes as this is classified
            let selected_allele = alleleSidebar.getSelectedAllele();
            alleleSectionBox.classifyAsT();
            let classification = alleleSidebar.getSelectedAlleleClassification();
            expect(classification).toBe('T', 'Unclassified should now be T');
            expect(alleleSidebar.isAlleleInClassified(selected_allele)).toBe(true);
        }

        // expect all to be classified
        expect(alleleSidebar.countOfUnclassified()).toBe(0);
        expect(alleleSidebar.countOfClassified()).toBe(numberOfClassifiedBefore + numberOfUnclassifiedBefore);

        // finalize
        analysisPage.finishButton.click();
        analysisPage.finalizeButton.click();

    });


    it('can navigate through interpretation rounds and see current official assessment', function() {
        // brca_e2e_test01.HBOCUTV_v01

        // given
        loginPage.selectThirdUser();
        overview.open();

        // when
        overview.selectFinished(1);

        // then
        expect(analysisPage.roundCount).toBe(2);

        const numberOfClassified = alleleSidebar.countOfClassified();
        expect(alleleSidebar.countOfUnclassified()).toBe(0);
        expect(numberOfClassified).toBeGreaterThan(1);

        // in last round all alleles was set to class 2
        for (let i=1; i<=numberOfClassified; i++) {
            alleleSidebar.selectClassifiedAlleleByIdx(i);
            let classification = alleleSidebar.getSelectedAlleleClassification();
            expect(classification).toBe('2', 'Class 2 for all alleles in newest (default) round');
        }

        // in first round all alleles was set to class 1
        analysisPage.chooseRound(1);
        for (let i=1; i<=numberOfClassified; i++) {
            alleleSidebar.selectClassifiedAlleleByIdx(i);
            let classification = alleleSidebar.getSelectedAlleleClassification();
            expect(classification).toBe('1', 'Class 1 for all alleles in first (oldest) round');
            expect(alleleSectionBox.hasExistingClassification()).toBe(false, 'no alleles from round one' +
                ' had an existing classification');
        }

        // in second (last) round all alleles was set to class 2
        analysisPage.chooseRound(2);
        for (let i=1; i<=numberOfClassified; i++) {
            alleleSidebar.selectClassifiedAlleleByIdx(i);
            let classification = alleleSidebar.getSelectedAlleleClassification();
            expect(classification).toBe('2', 'Class 2 for all alleles in newest (default) round');
            expect(alleleSectionBox.hasExistingClassification()).toBe(false, 'no alleles from round two' +
                ' had an existing classification');
        }


    });

    it('can see a (single) interpretation round and see current official assessment', function() {
        // brca_e2e_test02.HBOCUTV_v01
        loginPage.selectFirstUser();
        overview.open();
        overview.selectFinished(2);

        expect(analysisPage.roundCount).toBe(1);

        const numberOfUnclassified = alleleSidebar.countOfUnclassified();
        expect(numberOfUnclassified).toBe(0);
        const numberOfClassified = alleleSidebar.countOfClassified();
        expect(numberOfClassified).toBeGreaterThan(1);

        // expect all to be T, with existing classificaiton of 2 for some
        let numberOfAllelesWithExistingClassification = 0;
        for (let i=1; i<=numberOfClassified; i++) {
            alleleSidebar.selectClassifiedAlleleByIdx(i);
            let classification = alleleSidebar.getSelectedAlleleClassification();
            expect(classification).toBe('T', 'Technical for all alleles');
            if (alleleSectionBox.hasExistingClassification()) {
                expect(alleleSectionBox.getExistingClassificationClass()).toContain('Class 2', 'For variant with existing classification');
                numberOfAllelesWithExistingClassification += 1;
            }
        }
        expect(numberOfAllelesWithExistingClassification).toBeGreaterThan(1, 'At least one of the alleles should ' +
            'have had an existing classification at the time the current classification was done')

    });


});