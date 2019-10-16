require('core-js/fn/object/entries')

/**
 * Finalize two analyses, checking the interpretation rounds for the finished analyses:
 * 1. Sample 1, all classified as 1, set to review,
 * 2. Sample 1, , all classified as 2, finalization
 * 3. Sample 2: alleles overlap with previous sample 1, all classified as class U, finalize
 * 4. Open sample 1 (with two rounds). Check the rounds are different
 * 5. Open sample 2 (with one round). Check that some variants had an existing classification
 */

let LoginPage = require('../pageobjects/loginPage')
let SampleSelection = require('../pageobjects/overview_samples')
let AnalysisPage = require('../pageobjects/analysisPage')
let AlleleSidebar = require('../pageobjects/alleleSidebar')
let AlleleSectionBox = require('../pageobjects/alleleSectionBox')
let checkAlleleClassification = require('../helpers/checkAlleleClassification')
let failFast = require('jasmine-fail-fast')

let loginPage = new LoginPage()
let overview = new SampleSelection()
let analysisPage = new AnalysisPage()
let alleleSidebar = new AlleleSidebar()
let alleleSectionBox = new AlleleSectionBox()
const BUTTON_TEXT_REUSE_EXISTING_CLASSIFICATION = 'RE-EVALUATE'

const TITLE_INTERPRETATION = ' • INTERPRETATION'
const TITLE_REVIEW = ' • REVIEW'
const TITLE_MEDICAL_REVIEW = ' • MEDICAL REVIEW'

jasmine.getEnv().addReporter(failFast.init())

describe('Sample workflow ', function() {
    beforeAll(() => {
        browser.resetDb()
    })

    it('classifies variants and sets to review', function() {
        // brca_e2e_test01.HBOCUTV_v01
        loginPage.open()
        loginPage.selectFirstUser()
        overview.open()
        overview.selectWithMissingAssessments(1)
        analysisPage.startButton.click()

        expect(analysisPage.title).toBe('brca_e2e_test01.HBOCUTV_v01' + TITLE_INTERPRETATION)

        const numberOfUnclassified = alleleSidebar.countOfUnclassified()

        // Classify all as 1:
        for (let i = 1; i <= numberOfUnclassified; i++) {
            alleleSidebar.selectFirstUnclassified()
            let selected_allele = alleleSidebar.getSelectedAllele()
            alleleSectionBox.classifyAs1()
            expect(alleleSidebar.isAlleleInClassified(selected_allele)).toBe(true)
        }

        analysisPage.finishButton.click()
        analysisPage.markReviewButton.click()
        analysisPage.modalFinishButton.click()
    })

    it('reclassifies variants and sets to medical review', function() {
        // brca_e2e_test01.HBOCUTV_v01
        loginPage.open()
        loginPage.selectFirstUser()
        overview.open()
        overview.selectTopReview()
        analysisPage.startButton.click()

        expect(analysisPage.title).toBe('brca_e2e_test01.HBOCUTV_v01' + TITLE_REVIEW)

        analysisPage.selectSectionClassification()
        const numberOfClassifiedBefore = alleleSidebar.countOfClassified()
        expect(numberOfClassifiedBefore).toBeGreaterThan(0)
        expect(alleleSidebar.countOfUnclassified()).toBe(0)
        // All have Class 1 from previous round, now set to Class 2:
        for (let i = 1; i <= numberOfClassifiedBefore; i++) {
            let allele_element = alleleSidebar.selectClassifiedAlleleByIdx(i)
            let selected_allele = alleleSidebar.getSelectedAllele()
            expect(alleleSidebar.getSelectedAlleleClassification().current).toBe('1')
            alleleSectionBox.classifyAs2()
            browser.pause(100)
            expect(alleleSidebar.getSelectedAlleleClassification().current).toBe('2')
            expect(alleleSidebar.isAlleleInClassified(selected_allele)).toBe(true)
        }

        // expect all to be (still) classified
        expect(alleleSidebar.countOfUnclassified()).toBe(0)
        expect(alleleSidebar.countOfClassified()).toBe(numberOfClassifiedBefore)

        analysisPage.finishButton.click()
        analysisPage.markMedicalReviewButton.click()
        analysisPage.modalFinishButton.click()
    })

    it('can change classfications from previous round and finalize', function() {
        // brca_e2e_test01.HBOCUTV_v01
        loginPage.open()
        loginPage.selectSecondUser()
        overview.open()
        overview.selectTopMedicalReview()
        analysisPage.startButton.click()

        expect(analysisPage.title).toBe('brca_e2e_test01.HBOCUTV_v01' + TITLE_MEDICAL_REVIEW)

        const numberOfClassifiedBefore = alleleSidebar.countOfClassified()
        expect(numberOfClassifiedBefore).toBeGreaterThan(0)
        expect(alleleSidebar.countOfUnclassified()).toBe(0)

        analysisPage.selectSectionClassification()

        // All have Class 2 from previous round, now set to Class 3:
        for (let i = 1; i <= numberOfClassifiedBefore; i++) {
            let allele_element = alleleSidebar.selectClassifiedAlleleByIdx(i)
            let selected_allele = alleleSidebar.getSelectedAllele()
            expect(alleleSidebar.getSelectedAlleleClassification().current).toBe('2')
            alleleSectionBox.classifyAs3()
            expect(alleleSidebar.isAlleleInClassified(selected_allele)).toBe(true)
        }

        // expect all to be (still) classified
        expect(alleleSidebar.countOfUnclassified()).toBe(0)
        expect(alleleSidebar.countOfClassified()).toBe(numberOfClassifiedBefore)

        analysisPage.finishButton.click()
        analysisPage.finalizeButton.click()
        analysisPage.modalFinishButton.click()
    })

    it('shows existing classifications and finalize', function() {
        //  start a second analysis
        // brca_e2e_test02.HBOCUTV_v01
        loginPage.open()
        loginPage.selectThirdUser()
        overview.open()
        overview.selectWithMissingAssessments(1) // some variants assessed in another analysis
        analysisPage.startButton.click()

        expect(analysisPage.title).toBe('brca_e2e_test02.HBOCUTV_v01' + TITLE_INTERPRETATION)

        const numberOfUnclassifiedBefore = alleleSidebar.countOfUnclassified()
        const numberOfClassifiedBefore = alleleSidebar.countOfClassified()
        console.log(`2nd analysis, number of classified=${numberOfClassifiedBefore}`)
        console.log(`2nd analysis, number of unlassified=${numberOfUnclassifiedBefore}`)
        expect(numberOfClassifiedBefore).toBeGreaterThan(0)

        analysisPage.selectSectionClassification()

        // first classified allele have an existing classification:
        alleleSidebar.selectFirstClassified()
        alleleSectionBox.hasExistingClassification()
        expect(alleleSectionBox.getExistingClassificationClass()).toContain('Class 3')

        // Classify all as U:
        for (let i = 1; i <= numberOfClassifiedBefore; i++) {
            alleleSidebar.selectFirstClassified() // who's first changes when unclassify/classify
            let selected_allele = alleleSidebar.getSelectedAllele()
            expect(alleleSectionBox.classificationAcceptedToggleBtn.getText().toLowerCase()).toBe(
                BUTTON_TEXT_REUSE_EXISTING_CLASSIFICATION.toLowerCase(),
                'Allele should be marked as reusing existing classification'
            )
            alleleSectionBox.classificationAcceptedBtn.click()
            alleleSectionBox.classifyAsU()
            let classification = alleleSidebar.getSelectedAlleleClassification()
            expect(classification.existing).toBe('3')
            expect(classification.current).toBe('U')
            expect(alleleSidebar.isAlleleInClassified(selected_allele)).toBe(true)
        }

        for (let i = 1; i <= numberOfUnclassifiedBefore; i++) {
            alleleSidebar.selectFirstUnclassified() // who's first changes as this is classified
            let selected_allele = alleleSidebar.getSelectedAllele()
            alleleSectionBox.classifyAsU()
            let classification = alleleSidebar.getSelectedAlleleClassification()
            expect(classification.current).toBe('U', 'Unclassified should now be class U')
            expect(alleleSidebar.isAlleleInClassified(selected_allele)).toBe(true)
        }

        // expect all to be classified
        expect(alleleSidebar.countOfUnclassified()).toBe(0)
        expect(alleleSidebar.countOfClassified()).toBe(
            numberOfClassifiedBefore + numberOfUnclassifiedBefore
        )

        // finalize
        analysisPage.finishButton.click()
        analysisPage.finalizeButton.click()
        analysisPage.modalFinishButton.click()
    })

    it('can navigate through interpretation rounds and see current official assessment', function() {
        // brca_e2e_test01.HBOCUTV_v01

        // given
        loginPage.open()
        loginPage.selectThirdUser()
        overview.open()

        // when
        overview.selectFinished(2) // List is sorted desc, newest first

        // then
        expect(analysisPage.title).toBe('brca_e2e_test01.HBOCUTV_v01' + TITLE_MEDICAL_REVIEW)
        expect(analysisPage.getRounds().length).toBe(4) // 'Current data' "round" is added at end

        const numberOfClassified = alleleSidebar.countOfClassified()
        expect(alleleSidebar.countOfUnclassified()).toBe(0)
        expect(numberOfClassified).toBeGreaterThan(1)

        // current data round: Three alleles were classified as U in this sample, and two as 2 in the other sample

        let current_classifications = ['3', '3', 'U', 'U', 'U']
        for (let i = 1; i <= numberOfClassified; i++) {
            alleleSidebar.selectClassifiedAlleleByIdx(i)
            let classification = alleleSidebar.getSelectedAlleleClassification()
            expect(classification.current).toBe(
                current_classifications[i - 1],
                'Class matches for all alleles in current data (default) round'
            )
        }

        // in first round all alleles was set to class 1
        analysisPage.chooseRound(1)
        for (let i = 1; i <= numberOfClassified; i++) {
            alleleSidebar.selectClassifiedAlleleByIdx(i)
            let classification = alleleSidebar.getSelectedAlleleClassification()
            expect(classification.current).toBe('1')
            expect(alleleSectionBox.hasExistingClassification()).toBe(
                false,
                'no alleles from round one' + ' had an existing classification'
            )
        }

        // in second (last) round all alleles was set to class 2
        analysisPage.chooseRound(2)
        for (let i = 1; i <= numberOfClassified; i++) {
            alleleSidebar.selectClassifiedAlleleByIdx(i)
            let classification = alleleSidebar.getSelectedAlleleClassification()
            expect(classification.current).toBe('2', 'Class 2 for all alleles in second round')
            expect(alleleSectionBox.hasExistingClassification()).toBe(
                false,
                'no alleles from round two' + ' had an existing classification'
            )
        }

        analysisPage.chooseRound(3)
        for (let i = 1; i <= numberOfClassified; i++) {
            alleleSidebar.selectClassifiedAlleleByIdx(i)
            let classification = alleleSidebar.getSelectedAlleleClassification()
            expect(classification.current).toBe(
                '3',
                'Class 3 for all alleles in third (newest) round'
            )
            expect(alleleSectionBox.hasExistingClassification()).toBe(
                false,
                'no alleles from round three' + ' had an existing classification'
            )
        }
    })

    it('can see a (single) interpretation round and see current official assessment', function() {
        // brca_e2e_test02.HBOCUTV_v01
        loginPage.open()
        loginPage.selectFirstUser()
        overview.open()
        overview.selectFinished(1)

        expect(analysisPage.title).toBe('brca_e2e_test02.HBOCUTV_v01' + TITLE_INTERPRETATION)

        expect(analysisPage.getRounds().length).toBe(2)

        const numberOfUnclassified = alleleSidebar.countOfUnclassified()
        expect(numberOfUnclassified).toBe(0)
        const numberOfClassified = alleleSidebar.countOfClassified()
        expect(numberOfClassified).toBeGreaterThan(1)

        analysisPage.chooseRound(1)
        // expect all to be U, with existing classificaiton of 3 for some
        let numberOfAllelesWithExistingClassification = 0
        for (let i = 1; i <= numberOfClassified; i++) {
            alleleSidebar.selectClassifiedAlleleByIdx(i)
            let classification = alleleSidebar.getSelectedAlleleClassification()
            expect(classification.existing === '3' || classification.existing === '').toBe(true)
            expect(classification.current).toBe('U')
            if (alleleSectionBox.hasExistingClassification()) {
                expect(alleleSectionBox.getExistingClassificationClass()).toContain(
                    'Class 3',
                    'For variant with existing classification'
                )
                numberOfAllelesWithExistingClassification += 1
            }
        }
        expect(numberOfAllelesWithExistingClassification).toBeGreaterThan(
            1,
            'At least one of the alleles should ' +
                'have had an existing classification at the time the current classification was done'
        )
    })
})
