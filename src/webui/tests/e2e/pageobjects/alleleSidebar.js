var Page = require('./page')
let util = require('./util')

class AlleleSidebar extends Page {
    _ensureLoaded() {
        $('allele-sidebar .nav-row').waitForExist()
    }

    getUnclassifiedAlleles() {
        this._ensureLoaded()
        return $$('allele-sidebar .id-unclassified .nav-row .id-hgvsc').map((a) => a.getText())
    }

    getClassifiedAlleles() {
        this._ensureLoaded()
        return $$('allele-sidebar .id-classified .nav-row .id-hgvsc').map((a) => a.getText())
    }

    getNotRelevantAlleles() {
        this._ensureLoaded()
        return $$('allele-sidebar .id-notrelevant .nav-row .id-hgvsc').map((a) => a.getText())
    }

    getTechnicalAlleles() {
        this._ensureLoaded()
        return $$('allele-sidebar .id-technical .nav-row .id-hgvsc').map((a) => a.getText())
    }

    getSelectedAllele() {
        this._ensureLoaded()
        return $('allele-sidebar .nav-row.active .id-hgvsc').getText()
    }

    getSelectedAlleleClassification() {
        let e = $('allele-sidebar .nav-row.active')
        const current = e.$('.id-classification .current-classification').getText()
        const existing = e.$('.id-classification .existing-classification').getText()
        return {
            current: current,
            existing: existing
        }
    }

    _countOf(identifier) {
        this._ensureLoaded()
        const groupSelector = `allele-sidebar ${identifier} .nav-row.allele`
        return $$(groupSelector).map((a) => a.getText()).length
    }
    countOfUnclassified() {
        return this._countOf('.id-unclassified')
    }

    countOfClassified() {
        return this._countOf('.id-classified')
    }

    selectFirstUnclassified() {
        this._selectAlleleByIdx(1, '.id-unclassified')
    }

    selectFirstClassified() {
        this._selectAlleleByIdx(1, '.id-classified')
    }

    _getAlleleIdx(allele, identifier) {
        // example 'allele-sidebar .id-unclassified.enabled .nav-row .id-hgvsc'
        const all = $$(`allele-sidebar ${identifier} .nav-row .id-hgvsc`).map((a) => a.getText())
        const alleleIdx = all.findIndex((s) => s === allele)
        if (alleleIdx === -1) {
            throw Error(`Allele ${allele} not found among options ${all.join(',')}`)
        }
        return alleleIdx
    }

    _selectAllele(allele, identifier) {
        const alleleIdx = this._getAlleleIdx(allele, identifier)
        this._selectAlleleByIdx(alleleIdx + 1, identifier)
    }

    _selectAlleleByIdx(idx, identifier) {
        // 1-based
        this._ensureLoaded()
        let allele_selector = `allele-sidebar ${identifier} .nav-row:nth-child(${idx + 1})`
        $(allele_selector).click()

        // Check that we changed active allele
        expect(browser.getClass(allele_selector).find((a) => a === 'active')).toBeDefined()
        return $(allele_selector)
    }

    selectUnclassifiedAllele(allele) {
        this._selectAllele(allele, '.id-unclassified')
    }

    selectUnclassifiedAlleleByIdx(idx) {
        // 1-based
        // return this._selectAlleleByIdx(idx, '.id-unclassified')
        return this._selectAlleleByIdx(idx, '.id-unclassified')
    }

    selectClassifiedAllele(allele) {
        this._selectAllele(allele, '.id-classified')
    }

    selectClassifiedAlleleByIdx(idx) {
        // 1-based
        // return this._selectAlleleByIdx(idx, '.id-classified')
        return this._selectAlleleByIdx(idx, '.id-classified')
    }

    selectTechnicalAllele(allele) {
        this._selectAllele(allele, '.id-technical')
    }

    selectNotRelevantAllele(allele) {
        this._selectAllele(allele, '.id-notrelevant')
    }

    isAlleleInUnclassified(allele) {
        let a = this.getUnclassifiedAlleles()
        if (Array.isArray(a)) {
            return a.find((al) => al === allele) !== undefined
        }
        return a === allele
    }

    isAlleleInClassified(allele) {
        let a = this.getClassifiedAlleles()
        if (Array.isArray(a)) {
            return a.find((al) => al === allele) !== undefined
        }
        return a === allele
    }

    isAlleleInNotRelevant(allele) {
        let a = this.getNotRelevantAlleles()
        if (Array.isArray(a)) {
            return a.find((al) => al === allele) !== undefined
        }
        return a === allele
    }

    isAlleleInTechnical(allele) {
        let a = this.getTechnicalAlleles()
        if (Array.isArray(a)) {
            return a.find((al) => al === allele) !== undefined
        }
        return a === allele
    }

    open(page) {
        super.open('login')
    }

    isMarkedReviewed(allele) {
        const alleleIdx = this._getAlleleIdx(allele, '.id-classified')
        return Boolean(
            util.elementOrNull(
                `allele-sidebar .id-classified .nav-row:nth-child(${alleleIdx +
                    2}) .id-classification.reviewed`
            )
        )
    }

    markClassifiedReview(allele) {
        const alleleIdx = this._getAlleleIdx(allele, '.id-classified')
        $(
            `allele-sidebar .id-classified .nav-row:nth-child(${alleleIdx + 2}) .id-classification`
        ).click()
    }

    quickSetTechnical(allele) {
        const alleleIdx = this._getAlleleIdx(allele, '.id-unclassified')
        $(
            `allele-sidebar .id-unclassified .nav-row:nth-child(${alleleIdx +
                2}) .quick-classification .id-quick-technical`
        ).click()
    }

    quickSetNotRelevant(allele) {
        const alleleIdx = this._getAlleleIdx(allele, '.id-unclassified')
        $(
            `allele-sidebar .id-unclassified .nav-row:nth-child(${alleleIdx +
                2}) .quick-classification .id-quick-notrelevant`
        ).click()
    }

    quickClassU(allele) {
        const alleleIdx = this._getAlleleIdx(allele, '.id-unclassified')
        $(
            `allele-sidebar .id-unclassified .nav-row:nth-child(${alleleIdx +
                2}) .quick-classification .id-quick-classu`
        ).click()
    }

    quickClass2(allele) {
        const alleleIdx = this._getAlleleIdx(allele, '.id-unclassified')
        $(
            `allele-sidebar .id-unclassified .nav-row:nth-child(${alleleIdx +
                2}) .quick-classification .id-quick-class2`
        ).click()
    }

    _setComment(identifier, alleleIdx, text) {
        util.elementIntoView(
            `allele-sidebar ${identifier} .nav-row:nth-child(${alleleIdx + 2}) .evaluation`
        ).click()
        $(
            `allele-sidebar ${identifier} .nav-row:nth-child(${alleleIdx +
                2}) .evaluation .wysiwygeditor`
        ).setValue(text)
    }

    setEvaluationComment(allele, text) {
        const alleleIdx = this._getAlleleIdx(allele, '.id-classified')
        this._setComment('.id-classified', alleleIdx, text)
    }

    setTechnicalComment(allele, text) {
        const alleleIdx = this._getAlleleIdx(allele, '.id-technical')
        this._setComment('.id-technical', alleleIdx, text)
    }

    setNotRelevantComment(allele, text) {
        const alleleIdx = this._getAlleleIdx(allele, '.id-notrelevant')
        this._setComment('.id-notrelevant', alleleIdx, text)
    }
}

module.exports = AlleleSidebar
