var Page = require('./page')

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

    getSelectedAllele() {
        this._ensureLoaded()
        return browser.getText('allele-sidebar .nav-row.active .id-hgvsc')
    }

    getSelectedAlleleClassification() {
        // TODO: use method chaining to get classification from parent element
        let e = browser.element('allele-sidebar .nav-row.active')
        return e.getText('.id-classification')
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

    _selectAllele(allele, identifier) {
        // example 'allele-sidebar .id-unclassified.enabled .nav-row .id-hgvsc'
        let all = browser.getText(`allele-sidebar ${identifier} .nav-row .id-hgvsc`)
        let allele_idx = -1 // assume no match
        if (Array.isArray(all)) {
            allele_idx = all.findIndex((s) => s === allele)
        } else {
            // not an array, there is only one
            if (all === allele) {
                // match
                allele_idx = 0
            }
        }

        if (allele_idx === -1) {
            throw Error(`Allele ${allele} not found among options ${all.join(',')}`)
        }
        this._selectAlleleByIdx(allele_idx + 1, identifier)
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

    open(page) {
        super.open('login')
    }
}

module.exports = AlleleSidebar
