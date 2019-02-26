var Page = require('./page')
var util = require('./util')

const SELECTOR_ANALYSES_BY_FINDINGS = '#id-overview-sidenav-analyses-by-findings'
const SELECTOR_ANALYSES = '#id-overview-sidenav-analyses'
const SELECTOR_FINISHED = '.id-analysis-finished'
const SELECTOR_EMPTY = '.id-analysis-assessments-none'
const SELECTOR_ASSESSMENTS_MISSING = '.id-analysis-missing-classifications'
const SELECTOR_PENDING = '.id-analysis-pending'
const SELECTOR_REVIEW_FINDINGS = '.id-analysis-review-with-findings'
const SELECTOR_REVIEW_NORMAL = '.id-analysis-review-without-findings'
const SELECTOR_REVIEW_ASSESSMENTS_MISSING = '.id-analysis-review-missing-classifications'
const SELECTOR_REVIEW = SELECTOR_REVIEW_ASSESSMENTS_MISSING
const SELECTOR_MEDICALREVIEW = '.id-analysis-medicalreview'
const SELECTOR_NORMAL = '.id-analysis-findings-normal'
const SELECTOR_FINDINGS = '.id-analysis-findings'

//id-analysis-ours
// id-analysis-others

const SELECTOR_ANALYSIS_NAME = '.id-analysis-name'

const SECTION_EXPAND_SELECTOR = ' header .sb-title-container'

class SampleSelection extends Page {
    constructor(by_findings) {
        super()
        if (by_findings === undefined) {
            by_findings = true
        }
        this.by_findings = by_findings
    }
    open() {
        super.open('overview/')
        if (this.by_findings) {
            browser.waitForExist(SELECTOR_ANALYSES_BY_FINDINGS)
            browser.click(SELECTOR_ANALYSES_BY_FINDINGS)
        } else {
            browser.waitForExist(SELECTOR_ANALYSES)
            browser.click(SELECTOR_ANALYSES)
        }
        // We need to make sure that the page is loaded.
        // waitForExist(#nprogress) doesn't work well here, since it sometimes is so quick that it's missed
        // Pause instead and then make sure the loading is gone
        browser.pause(100)
        browser.waitForExist('#nprogress', 10000, true) // Make sure loading is done before proceeding
    }

    get analysisList() {
        return util.element('analysis-list')
    }
    get noFindingsSection() {
        return util.element('.id-analysis-findings-none')
    }
    get findingsSection() {
        return util.element(SELECTOR_FINDINGS)
    }
    get emptySection() {
        return util.element(SELECTOR_EMPTY)
    }
    get pendingSection() {
        return util.element(SELECTOR_PENDING)
    }
    get reviewSection() {
        return util.element(SELECTOR_REVIEW)
    }
    get finishedSection() {
        return util.element(SELECTOR_FINISHED)
    }

    get normalSection() {
        return util.element(SELECTOR_NORMAL)
    }

    expandPendingSection() {
        this._expandSection(SELECTOR_PENDING)
    }

    expandReviewSection() {
        this._expandSection(SELECTOR_REVIEW)
    }

    _expandSection(sectionSelector) {
        this.open()
        browser.waitForExist(sectionSelector)
        // Expand if collapsed
        if (browser.isExisting(sectionSelector + ' .collapsed')) {
            browser.click(sectionSelector + SECTION_EXPAND_SELECTOR)
        }
    }

    selectItemInSection(number, sectionSelector) {
        this.open()
        // expand box:
        browser.waitForExist(sectionSelector)

        // Expand if collapsed
        if (browser.isExisting(sectionSelector + '.collapsed')) {
            browser.click(sectionSelector + SECTION_EXPAND_SELECTOR)
        }
        let selector = `${sectionSelector} .id-analysis:nth-child(${number})`
        // console.log('Going to click selector:' + selector);
        browser.waitForExist(selector)
        browser.click(selector)
        let element = browser.element(selector)
        browser.waitForExist('analysis-list', 5000, true)
        return element
    }

    selectFinished(number) {
        this.selectItemInSection(number, SELECTOR_FINISHED)
    }

    selectPending(number, name) {
        let analysisWrapper = this.selectItemInSection(number, SELECTOR_PENDING)
        // attempt to validate the chosen element matches the name:
        // This fails with a Cannot read property 'ELEMENT' of null
        // let analysisNameElement = analysisWrapper.element(SELECTOR_ANALYSIS_NAME);
        //
        // if (name) {
        //     actualName = analysisNameElement.getText();
        //     if (name === actualName) {
        //         OK
        // } else {
        //     console.error("Analysis name mismatch");
        // }
        // }
    }

    selectWithMissingAssessments(number, name) {
        let analysisWrapper = this.selectItemInSection(number, SELECTOR_ASSESSMENTS_MISSING)
    }

    selectReview(number) {
        if (this.by_findings) {
            this.selectItemInSection(number, SELECTOR_REVIEW)
        } else {
            this.selectItemInSection(number, '.id-analysis-review')
        }
    }

    selectMedicalReview(number) {
        this.selectItemInSection(number, SELECTOR_MEDICALREVIEW)
    }

    selectFindingsNormal(number) {
        this.selectItemInSection(number, SELECTOR_NORMAL)
    }

    selectFindings(number) {
        this.selectItemInSection(number, SELECTOR_FINDINGS)
    }

    selectTopPending() {
        this.selectPending(1)
    }

    selectTopReview() {
        this.selectReview(1)
    }

    selectTopMedicalReview() {
        this.selectMedicalReview(1)
    }

    getReviewTags() {
        // no ui showing tags!
        return browser.getText(`${SELECTOR_REVIEW} .analysis-extras .tag`)
    }

    getReviewComment() {
        let selector = `${SELECTOR_REVIEW} .analysis-extras .id-analysis-comment`
        return browser.getText(selector)
    }
}

module.exports = SampleSelection
