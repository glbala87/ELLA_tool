var Page = require('./page')
var util = require('./util')

const SELECTOR_ANALYSES_OVERVIEW = '#id-overview-sidenav-analyses'
const SELECTOR_FINISHED = '.id-analysis-finished'
const SELECTOR_EMPTY = '.id-analysis-assessments-none'
const SELECTOR_PENDING = '.id-analysis-pending'
const SELECTOR_REVIEW = '.id-analysis-review'
const SELECTOR_MEDICALREVIEW = '.id-analysis-medicalreview'
const SELECTOR_OURS = '.id-analysis-ours'
const SELECTOR_OTHERS = '.id-analysis-others'
const SELECTOR_CLASSIFIED = '.id-analysis-classified'

// acceptable filter values
const PRIORITY_LEVELS = ['normal', 'high', 'urgent']
const FILTER_TECHNOLOGIES = ['Sanger', 'HTS']
const FILTER_RANGES = new RegExp('^[gl][te]:-?\\d+:[dm]$')

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

    filterAnalysisName(nameText) {
        $('.id-overview-filter-analysis-name').setValue(nameText)
    }

    filterReviewComment(commentText) {
        $('.id-overview-filter-review-comment').setValue(commentText)
    }

    toggleFilterTechnology(technologyType) {
        if (FILTER_TECHNOLOGIES.indexOf(technologyType) > -1) {
            $(`.id-overview-filter-technology-${technologyType.toLowerCase()}`).click()
        } else {
            throw new TypeError(`Invalid technology type ${technologyType}`)
        }
    }

    toggleFilterPriority(priorityLevel) {
        if (PRIORITY_LEVELS.indexOf(priorityLevel) > -1) {
            $(`.id-overview-filter-priority-${priorityLevel}`).click()
        } else {
            throw new TypeError(`Invalid priority level: ${priorityLevel}`)
        }
    }

    filterDateRange(dateString) {
        if (FILTER_RANGES.test(dateString)) {
            $('.id-overview-filter-date-range').selectByAttribute('value', dateString)
        } else {
            throw new TypeError(`Invalid dateRange: ${dateString}`)
        }
    }

    filterClear() {
        $('.id-clear-filter').click()
    }

    get filteredAnalyses() {
        // flatten all analyses into a single array
        const analysesByType = $$('analysis-list').map((a) => a.$$('.id-analysis'))
        return [].concat.apply([], analysesByType)
    }

    get analysisList() {
        return util.element('analysis-list')
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
        // Wait for workflow to fully load
        $('.id-workflow-instance').waitForExist()
        $('#nprogress').waitForExist(undefined, true)
        return el
    }

    selectFinished(number) {
        this.selectItemInSection(number, SELECTOR_FINISHED)
    }

    selectPending(number, name) {
        this.selectItemInSection(number, SELECTOR_PENDING)
    }

    selectReview(number) {
        this.selectItemInSection(number, SELECTOR_REVIEW)
    }

    selectMedicalReview(number) {
        this.selectItemInSection(number, SELECTOR_MEDICALREVIEW)
    }

    selectOthers(number) {
        this.selectItemInSection(number, SELECTOR_OTHERS)
    }

    selectOurs(number) {
        this.selectItemInSection(number, SELECTOR_OURS)
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
