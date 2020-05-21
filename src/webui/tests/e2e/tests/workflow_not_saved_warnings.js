require('core-js/fn/object/entries')

/**
 * Checks that collision warning is displayed when starting interpretation with variants that overlap another
 * ongoing interpretation
 */

const Page = require('../pageobjects/page')
const LoginPage = require('../pageobjects/loginPage')
const SampleSelectionPage = require('../pageobjects/overview_samples')
const AnalysisPage = require('../pageobjects/analysisPage')
const AlleleSectionBox = require('../pageobjects/alleleSectionBox')

const loginPage = new LoginPage()
const analysesSelectionPage = new SampleSelectionPage()
const analysisPage = new AnalysisPage()
const alleleSectionBox = new AlleleSectionBox()

var failFast = require('jasmine-fail-fast')

describe('Sample workflow', function() {
    beforeAll(() => {
        browser.resetDb()
    })

    it('gives warning when user has unsaved work and tries to navigate away', function() {
        // sample 1
        loginPage.open()
        loginPage.loginAs('testuser1')
        analysesSelectionPage.selectTopPending()
        analysisPage.startButton.click()

        // Check both types of warnings
        // No changes -> no warning should be shown
        analysesSelectionPage.selectOurs(1)

        // Make sure loading is done before proceeding
        browser.pause(500)
        $('#nprogress').waitForExist(undefined, true)

        analysisPage.overviewLink.click()
        analysesSelectionPage.selectOurs(1)

        browser.pause(500)
        $('#nprogress').waitForExist(undefined, true)

        // Modify the analysis specific comment
        alleleSectionBox.setAnalysisSpecificComment('Some text')

        // Try URL navigation
        new Page().open('overview/')
        browser.pause(1000)
        expect(browser.getAlertText()).toEqual('') // Will throw 'no such alert' if missing
        browser.dismissAlert()

        // Try pushState navigation
        analysisPage.overviewLink.click()
        browser.pause(1000)
        expect(browser.getAlertText()).toEqual(
            'You have unsaved work. Are you sure you want to leave the page? Any unsaved changes will be lost.'
        )
        browser.dismissAlert()

        // Save and re-check
        analysisPage.saveButton.click()

        analysesSelectionPage.open()
        browser.back()

        browser.pause(500)
        $('#nprogress').waitForExist(undefined, true)

        analysisPage.overviewLink.click()
        analysesSelectionPage.selectOurs(1)

        browser.pause(500)
        $('#nprogress').waitForExist(undefined, true)
    })
})
