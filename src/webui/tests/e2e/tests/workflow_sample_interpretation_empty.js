require('core-js/fn/object/entries')

/**
 * Make sure an empty analysis loads, can be started, moved to different
 * workflow step ("Finish", send to e.g. "Review") and finalized.
 * Test sections: INFO, CLASSIFICATION and REPORT.
 */

let LoginPage = require('../pageobjects/loginPage')
let SampleSelection = require('../pageobjects/overview_samples')
let AnalysisPage = require('../pageobjects/analysisPage')

let loginPage = new LoginPage()
let overview = new SampleSelection()
let analysisPage = new AnalysisPage()

const TITLE_INTERPRETATION = ' • INTERPRETATION'
const TITLE_REVIEW = ' • REVIEW'
const TITLE_MEDICAL_REVIEW = ' • MEDICAL REVIEW'
const ANALYSIS_NAME = 'brca_e2e_test04.HBOCUTV_v1.0'

describe('Sample workflow with an empty anaysis', function() {
    beforeAll(() => {
        browser.resetDb()
    })

    it(`sets empty analysis (${ANALYSIS_NAME}) to review`, function() {
        loginPage.open()
        loginPage.loginAs('testuser1')
        overview.open()
        overview.selectPending(4)
        expect(analysisPage.title).toBe(ANALYSIS_NAME + TITLE_INTERPRETATION)
        console.log('Changing to report page')
        analysisPage.selectSectionReport()
        console.log('Changing to info page')
        analysisPage.selectSectionInfo()
        console.log('Changing to classification page')
        analysisPage.selectSectionClassification()
        analysisPage.startButton.click()
        analysisPage.finishButton.click()
        analysisPage.markReviewButton.click()
        analysisPage.modalFinishButton.click()
    })

    it(`sets empty analysis (${ANALYSIS_NAME}) to medical review`, function() {
        loginPage.open()
        loginPage.loginAs('testuser1')
        overview.open()
        overview.selectTopReview()
        expect(analysisPage.title).toBe(ANALYSIS_NAME + TITLE_REVIEW)
        console.log('Changing to report page')
        analysisPage.selectSectionReport()
        console.log('Changing to info page')
        analysisPage.selectSectionInfo()
        console.log('Changing to classification page')
        analysisPage.selectSectionClassification()
        analysisPage.startButton.click()
        analysisPage.finishButton.click()
        analysisPage.markMedicalReviewButton.click()
        analysisPage.modalFinishButton.click()
    })

    it(`sets empty analysis (${ANALYSIS_NAME}) to finalized`, function() {
        loginPage.open()
        loginPage.loginAs('testuser1')
        overview.open()
        overview.selectTopMedicalReview()
        expect(analysisPage.title).toBe(ANALYSIS_NAME + TITLE_MEDICAL_REVIEW)
        console.log('Changing to report page')
        analysisPage.selectSectionReport()
        console.log('Changing to info page')
        analysisPage.selectSectionInfo()
        console.log('Changing to classification page')
        analysisPage.selectSectionClassification()
        analysisPage.startButton.click()
        analysisPage.finishButton.click()
        analysisPage.finalizeButton.click()
        analysisPage.modalFinishButton.click()
    })

    it(`select empty finished analysis (${ANALYSIS_NAME})`, function() {
        loginPage.open()
        loginPage.loginAs('testuser1')
        overview.open()
        overview.selectFinished(1)
        expect(analysisPage.title).toBe(ANALYSIS_NAME + TITLE_MEDICAL_REVIEW)
        console.log('Changing to report page')
        analysisPage.selectSectionReport()
        console.log('Changing to info page')
        analysisPage.selectSectionInfo()
        console.log('Changing to classification page')
        analysisPage.selectSectionClassification()
    })

    it(`cycle through old interpretations (${ANALYSIS_NAME})`, function() {
        loginPage.open()
        loginPage.loginAs('testuser1')
        overview.open()
        overview.selectFinished(1)
        expect(analysisPage.getRounds().length).toBe(4) // 'Current data' "round" is added at end
        analysisPage.chooseRound(4) // current
        analysisPage.chooseRound(3)
        analysisPage.chooseRound(2)
        analysisPage.chooseRound(1)
    })
})
