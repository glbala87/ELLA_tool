let Page = require('./page')
let util = require('./util')

const SELECTOR_OVERVIEW_VARIANTS = '#id-overview-sidenav-variants'
const SELECTOR_FINISHED = '.id-variants-finished'
const SELECTOR_PENDING = '.id-variants-pending' // no assessment
const SELECTOR_REVIEW = '.id-variants-review'
const SELECTOR_YOURS = '.id-variants-your'
const SELECTOR_OTHERS = '.id-variants-others'

const SELECTOR_VARIANT_NAME = '.id-variant-name'

const SECTION_EXPAND_SELECTOR = ' header .sb-title-container'

class VariantSelection extends Page {
    open() {
        super.open('overview/')
        const el = $(SELECTOR_OVERVIEW_VARIANTS)
        el.waitForExist()
        el.click()
        $('#nprogress').waitForExist(undefined, true) // Make sure loading is done before proceeding
    }

    get variantList() {
        return $('allele-list')
    }
    get yoursSection() {
        return $(SELECTOR_YOURS)
    }
    get othersSection() {
        return $(SELECTOR_OTHERS)
    }
    get pendingSection() {
        return $(SELECTOR_PENDING)
    }
    get reviewSection() {
        return $(SELECTOR_REVIEW)
    }
    get finishedSection() {
        return $(SELECTOR_FINISHED)
    }

    variantNamePending(number) {
        let selector = `${SELECTOR_PENDING} .id-variant:nth-child(${number})`
        return $(`${selector} .id-variant-name`).getText()
    }

    expandPendingSection() {
        this._expandSection(SELECTOR_PENDING)
    }

    expandReviewSection() {
        this._expandSection(SELECTOR_REVIEW)
    }

    expandFinishedSection() {
        this._expandSection(SELECTOR_FINISHED)
    }

    expandOthersSection() {
        this._expandSection(SELECTOR_OTHERS)
    }

    expandOwnSection() {
        this._expandSection(SELECTOR_YOURS)
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
        this._expandSection(sectionSelector)
        let selector = `${sectionSelector} .id-variant:nth-child(${number})`
        const el = $(selector)
        el.waitForExist()
        el.click()
        $('allele-list').waitForExist(undefined, true)
        return el
    }

    selectFinished(number) {
        this.selectItemInSection(number, SELECTOR_FINISHED)
    }

    selectPending(number) {
        this.selectItemInSection(number, SELECTOR_PENDING)
    }

    selectReview(number) {
        this.selectItemInSection(number, SELECTOR_REVIEW)
    }

    selectFinished(number) {
        this.selectItemInSection(number, SELECTOR_FINISHED)
    }

    selectOwn(number) {
        this.selectItemInSection(number, SELECTOR_YOURS)
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

    selectTopFinished() {
        this.selectFinished(1)
    }

    getReviewComment() {
        let selector = `${SELECTOR_REVIEW} .allele-extras .id-allele-comment`
        return $(selector).getText()
    }
}

module.exports = VariantSelection
