var Page = require('./page')
let util = require('./util')

class AlleleSidebar extends Page {
    _ensureLoaded() {
        browser.waitForExist('allele-sidebar .nav-row')
    }

    getUnclassifiedAlleles() {
        this._ensureLoaded()
        return browser.getText('allele-sidebar .id-unclassified .nav-row .id-hgvsc')
    }

    getClassifiedAlleles() {
        this._ensureLoaded()
        return browser.getText('allele-sidebar .id-classified .nav-row .id-hgvsc')
    }

    getNotRelevantAlleles() {
        this._ensureLoaded()
        return browser.getText('allele-sidebar .id-notrelevant .nav-row .id-hgvsc')
    }

    getTechnicalAlleles() {
        this._ensureLoaded()
        return browser.getText('allele-sidebar .id-technical .nav-row .id-hgvsc')
    }

    getSelectedAllele() {
        this._ensureLoaded()
        return browser.getText('allele-sidebar .nav-row.active .id-hgvsc')
    }

    getSelectedAlleleClassification() {
        let e = browser.element('allele-sidebar .nav-row.active')
        const current = e.getText('.id-classification .current-classification')
        const existing = e.getText('.id-classification .existing-classification')
        return {
            current: current,
            existing: existing
        }
    }

    _countOf(identifier) {
        this._ensureLoaded()
        const groupSelector = `allele-sidebar ${identifier} .nav-row.allele`
        if (!browser.isExisting(groupSelector)) {
            return 0
        }
        let all = browser.getText(groupSelector)
        if (Array.isArray(all)) {
            return all.length
        } else {
            return 1 // if zero an exception would be called above
        }
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
        let all = browser.getText(`allele-sidebar ${identifier} .nav-row .id-hgvsc`)
        let alleleIdx = -1 // assume no match
        if (Array.isArray(all)) {
            alleleIdx = all.findIndex((s) => s === allele)
        } else {
            // not an array, there is only one
            if (all === allele) {
                // match
                alleleIdx = 0
            }
        }

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
        browser.click(allele_selector)

        // Check that we changed active allele
        expect(browser.getClass(allele_selector).find((a) => a === 'active')).toBeDefined()
        return browser.element(allele_selector)
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
        browser.click(
            `allele-sidebar .id-classified .nav-row:nth-child(${alleleIdx + 2}) .id-classification`
        )
    }

    quickSetTechnical(allele) {
        const alleleIdx = this._getAlleleIdx(allele, '.id-unclassified')
        browser.click(
            `allele-sidebar .id-unclassified .nav-row:nth-child(${alleleIdx +
                2}) .quick-classification .id-quick-technical`
        )
    }

    quickSetNotRelevant(allele) {
        const alleleIdx = this._getAlleleIdx(allele, '.id-unclassified')
        browser.click(
            `allele-sidebar .id-unclassified .nav-row:nth-child(${alleleIdx +
                2}) .quick-classification .id-quick-notrelevant`
        )
    }

    quickClassU(allele) {
        const alleleIdx = this._getAlleleIdx(allele, '.id-unclassified')
        browser.click(
            `allele-sidebar .id-unclassified .nav-row:nth-child(${alleleIdx +
                2}) .quick-classification .id-quick-classu`
        )
    }

    quickClass2(allele) {
        const alleleIdx = this._getAlleleIdx(allele, '.id-unclassified')
        browser.click(
            `allele-sidebar .id-unclassified .nav-row:nth-child(${alleleIdx +
                2}) .quick-classification .id-quick-class2`
        )
    }

    _setComment(identifier, alleleIdx, text) {
        util.elementIntoView(
            `allele-sidebar ${identifier} .nav-row:nth-child(${alleleIdx + 2}) .evaluation`
        ).click()
        browser.setValue(
            `allele-sidebar ${identifier} .nav-row:nth-child(${alleleIdx +
                2}) .evaluation .wysiwygeditor`,
            text
        )
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
