var Page = require('./page')
var util = require('./util')

const SELECTOR_ANALYSES_OVERVIEW = '#id-overview-sidenav-analyses-by-classified'
const SELECTOR_FINISHED = '.id-analysis-finished'
const SELECTOR_EMPTY = '.id-analysis-assessments-none'
const SELECTOR_ASSESSMENTS_MISSING = '.id-analysis-missing-classifications'
const SELECTOR_PENDING = SELECTOR_ASSESSMENTS_MISSING
const SELECTOR_REVIEW_ASSESSMENTS_MISSING = '.id-analysis-review-missing-classifications'
const SELECTOR_REVIEW = SELECTOR_REVIEW_ASSESSMENTS_MISSING
const SELECTOR_MEDICALREVIEW = '.id-analysis-medicalreview'
const SELECTOR_OTHERS = '.id-analysis-others'
const SELECTOR_CLASSIFIED = '.id-analysis-classified'

//id-analysis-ours
// id-analysis-others

const SELECTOR_ANALYSIS_NAME = '.id-analysis-name'

const SECTION_EXPAND_SELECTOR = ' header .sb-title-container'

class SampleSelection extends Page {
    open() {
        super.open('overview/')
        const el = $(SELECTOR_ANALYSES_OVERVIEW)
        el.waitForExist()
        el.click()
        // We need to make sure that the page is loaded.
        // waitForExist(#nprogress) doesn't work well here, since it sometimes is so quick that it's missed
        // Pause instead and then make sure the loading is gone
        browser.pause(100)
        $('#nprogress').waitForExist(undefined, true) // Make sure loading is done before proceeding
    }

    get analysisList() {
        return util.element('analysis-list')
    }
    get noClassifiedSection() {
        return util.element('.id-analysis-classified-none')
    }
    get classifiedSection() {
        return util.element(SELECTOR_CLASSIFIED)
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

    expandPendingSection() {
        this._expandSection(SELECTOR_PENDING)
    }

    expandReviewSection() {
        this._expandSection(SELECTOR_REVIEW)
    }

    _expandSection(sectionSelector) {
        this.open()
        $(sectionSelector).waitForExist()
        // Expand if collapsed
        if ($(sectionSelector + ' .collapsed').isExisting()) {
            $(sectionSelector + SECTION_EXPAND_SELECTOR).click()
        }
    }

    selectItemInSection(number, sectionSelector) {
        this.open()
        // expand box:
        $(sectionSelector).waitForExist()

        // Expand if collapsed
        if ($(sectionSelector + '.collapsed').isExisting()) {
            $(sectionSelector + SECTION_EXPAND_SELECTOR).click()
        }
        let selector = `${sectionSelector} .id-analysis:nth-child(${number})`
        const el = $(selector)
        el.waitForExist()
        el.click()
        $('analysis-list').waitForExist(undefined, true)
        return el
    }

    selectFinished(number) {
        this.selectItemInSection(number, SELECTOR_FINISHED)
    }

    selectPending(number, name) {
        this.selectItemInSection(number, SELECTOR_PENDING)
    }

    selectWithMissingAssessments(number, name) {
        this.selectItemInSection(number, SELECTOR_ASSESSMENTS_MISSING)
    }

    selectReview(number) {
        this.selectItemInSection(number, SELECTOR_REVIEW)
    }

    selectMedicalReview(number) {
        this.selectItemInSection(number, SELECTOR_MEDICALREVIEW)
    }

    selectClassifiedNormal(number) {
        this.selectItemInSection(number, SELECTOR_NORMAL)
    }

    selectClassified(number) {
        this.selectItemInSection(number, SELECTOR_CLASSIFIED)
    }

    selectOthers(number) {
        this.selectItemInSection(number, SELECTOR_OTHERS)
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
        return $$(`${SELECTOR_REVIEW} .analysis-extras .tag`).map((a) => a.getText())
    }

    getReviewComment() {
        let selector = `${SELECTOR_REVIEW} .analysis-extras .id-analysis-comment`
        return $(selector).getText()
    }
}

module.exports = SampleSelection
