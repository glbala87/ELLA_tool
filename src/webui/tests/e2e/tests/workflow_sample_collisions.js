require('core-js/fn/object/entries')

/**
 * Checks that collision warning is displayed when starting interpretation with variants that overlap another
 * ongoing interpretation
 */

let LoginPage = require('../pageobjects/loginPage')
let SampleSelectionPage = require('../pageobjects/overview_samples')
let AnalysisPage = require('../pageobjects/analysisPage')

let loginPage = new LoginPage()
let analysesSelectionPage = new SampleSelectionPage()
let analysisPage = new AnalysisPage()

var failFast = require('jasmine-fail-fast')
jasmine.getEnv().addReporter(failFast.init())

describe('Sample workflow', function() {
    beforeAll(() => {
        browser.resetDb()
    })

    it('gives warning when starting a sample with variants that overlap with other ongoing sample', function() {
        // sample 1
        loginPage.open()
        loginPage.selectFirstUser()
        analysesSelectionPage.selectTopPending()
        analysisPage.startButton.click()

        // sample 2
        loginPage.open()
        browser.acceptAlert()
        loginPage.selectSecondUser()
        analysesSelectionPage.selectTopPending()
        analysisPage.collisionWarningBar.waitForExist()
    })
})
