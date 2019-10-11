require('core-js/fn/object/entries')

/**
 * Checks if the interpretation page is read-only in the correct situations
 */

let LoginPage = require('../pageobjects/loginPage')
let VariantSelectionPage = require('../pageobjects/overview_variants')
let AnalysisPage = require('../pageobjects/analysisPage')
let AlleleSectionBox = require('../pageobjects/alleleSectionBox')
let failFast = require('jasmine-fail-fast')

let loginPage = new LoginPage()
let variantSelectionPage = new VariantSelectionPage()
let analysisPage = new AnalysisPage()
let alleleSectionBox = new AlleleSectionBox()

jasmine.getEnv().addReporter(failFast.init())

const OUR_VARIANT = 'c.581G>A'

describe('Read-only version of variant workflow ', function() {
    beforeAll(() => {
        browser.resetDb()
    })

    it('A pending variant that is started is editable', function() {
        loginPage.open()
        loginPage.selectFirstUser()
        variantSelectionPage.selectPending(5)
        analysisPage.startButton.click()

        alleleSectionBox.classifyAs1()

        analysisPage.saveButton.click()
    })

    it("others' ongoing work is read-only", function() {
        loginPage.open()
        loginPage.selectSecondUser()
        variantSelectionPage.expandOthersSection()
        variantSelectionPage.selectOthers(1)
        expect(alleleSectionBox.classSelection.isEnabled()).toBe(false)
    })

    it('own ongoing work is writeable', function() {
        loginPage.open()
        loginPage.selectFirstUser()
        variantSelectionPage.expandOwnSection()
        variantSelectionPage.selectOwn(1)

        expect(alleleSectionBox.isClass1()).toBe(true)

        expect(alleleSectionBox.classSelection.isEnabled()).toBe(true)
    })

    it('others review is read-only until started', function() {
        // own classifies as class1 and sets to review
        loginPage.open()
        loginPage.selectFirstUser()
        variantSelectionPage.expandOwnSection()
        variantSelectionPage.selectOwn(1)
        alleleSectionBox.classifyAs2()
        analysisPage.finishButton.click()
        analysisPage.markReviewButton.click()
        analysisPage.modalFinishButton.click()

        // other user see a read-only
        loginPage.open()
        loginPage.selectSecondUser()
        variantSelectionPage.expandReviewSection()
        variantSelectionPage.selectReview(1)

        expect(alleleSectionBox.classSelection.isEnabled()).toBe(false)
        expect(alleleSectionBox.isClass2()).toBe(true)

        // other user starts a review
        analysisPage.startButton.click()
        expect(alleleSectionBox.classSelection.isEnabled()).toBe(true)
        analysisPage.finishButton.click()
        analysisPage.finalizeButton.click()
        analysisPage.modalFinishButton.click()
    })

    it('finalized is read-only until reopened and review is started', function() {
        loginPage.selectThirdUser()
        variantSelectionPage.expandFinishedSection()
        variantSelectionPage.selectFinished(1)

        expect(alleleSectionBox.classSelection.isEnabled()).toBe(false)

        analysisPage.reopenButton.click()
        expect(alleleSectionBox.classSelection.isEnabled()).toBe(false)

        analysisPage.startButton.click()
        expect(alleleSectionBox.classSelection.isEnabled()).toBe(false)

        alleleSectionBox.classificationAcceptedToggleBtn.click()
        expect(alleleSectionBox.classSelection.isEnabled()).toBe(true)
        alleleSectionBox.classifyAs2()

        analysisPage.finishButton.click()
        analysisPage.finalizeButton.click()
        analysisPage.modalFinishButton.click()
    })

    it('finalized is read-only, but report is editable', function() {
        loginPage.selectThirdUser()
        variantSelectionPage.expandFinishedSection()
        variantSelectionPage.selectFinished(1)

        alleleSectionBox.reportCommentElement.click()
        expect(alleleSectionBox.reportCommentEditable).toBe(false)

        analysisPage.startButton.click()
        alleleSectionBox.reportCommentElement.click()
        expect(alleleSectionBox.reportCommentEditable).toBe(true)
        $('body').click() // a trick to unfocus the above report comment

        alleleSectionBox.setReportComment('report changed')
        analysisPage.finishButton.click()
        analysisPage.finalizeButton.click()
        analysisPage.modalFinishButton.click()

        loginPage.open()
        loginPage.selectSecondUser()
        variantSelectionPage.expandFinishedSection()
        variantSelectionPage.selectFinished(1)
        alleleSectionBox.reportCommentElement.click()
        expect(alleleSectionBox.reportCommentEditable).toBe(false)
        expect(alleleSectionBox.reportComment).toBe('report changed')
    })
})
