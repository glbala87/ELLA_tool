var Page = require('./page')


class AlleleSidebar extends Page {

    _ensureLoaded() {
        browser.waitForExist('allele-sidebar .nav-row');
    }

    getUnclassifiedAlleles() {
        this._ensureLoaded();
        return browser.getText('allele-sidebar .id-unclassified.enabled .nav-row .id-hgvsc');
    }

    getClassifiedAlleles() {
        this._ensureLoaded();
        return browser.getText('allele-sidebar .id-classified.enabled .nav-row .id-hgvsc');
    }

    getSelectedAllele() {
        this._ensureLoaded();
        return browser.getText('allele-sidebar .enabled .nav-row.active .id-hgvsc');
    }

    getSelectedAlleleClassification() { // TODO: use method chaining to get classification from parent element
        let e =  browser.element('allele-sidebar .enabled .nav-row.active');
        return e.getText('.id-classification');
    }



    _countOf(identifier) {
        this._ensureLoaded();
        const groupSelector = `allele-sidebar ${identifier} .nav-row`;
        if (!browser.isExisting(groupSelector)) {
            return 0;
        }
        let all = browser.getText(groupSelector);
        if (Array.isArray(all)) {
            return all.length;
        } else {
            return 1; // if zero an exception would be called above
        }


    }
    countOfUnclassified() {
        return this._countOf('.id-unclassified');
    }

    countOfClassified() {
        return this._countOf('.id-classified');
    }

    selectFirstUnclassifedForce() {
        this._selectFirstInForced('.id-unclassified');
    }

    selectFirstClassifiedForce() {
        this._selectFirstInForced('.id-classified');
    }

    selectClassified(number) {
        return this._selectAlleleNumber(number, '.id-classified');
    }

    selectUnclassified(number) {
        return this._selectAlleleNumber(number, '.id-unclassified');
    }

    _selectFirstInForced(identifier) { // selectFirstUnclassified throws an error if there is less than two!
        this._ensureLoaded();
        const groupSelector = `allele-sidebar ${identifier} .nav-row`;
        let all = browser.getText(groupSelector);
        if (Array.isArray(all)) {
            let selector_of_first = `${groupSelector}:nth-child(1)`;
            browser.click(selector_of_first);
        } else {
            browser.click(groupSelector);
        }
        return;
    }
    selectFirstUnclassified() {
        this._selectFirstIn('.id-unclassified.enabled');
    }

    selectFirstClassified() {
        this._selectFirstIn('.id-classified.enabled');
    }

    _selectFirstIn(identifier) {
        this._ensureLoaded();
        const groupSelector = `allele-sidebar ${identifier} .nav-row`;
        let all = browser.getText(groupSelector);
        if (Array.isArray(all)) {
            let selector_of_first = `${groupSelector}:nth-child(1)`;
            browser.click(selector_of_first);
            return;
        }
        throw Error(`Using selector '${groupSelector}' didn't result in an Array`);
        }

    _selectAlleleNumber(number, identifier) {
        this._ensureLoaded();
        const allele_selector = `allele-sidebar ${identifier} .nav-row:nth-child(${number})`;
        browser.click(allele_selector);

        // Check that we changed active allele
        expect(browser.getClass(allele_selector).find(a => a === 'active')).toBeDefined();
        return browser.element(allele_selector);
    }

    _selectAllele(allele, identifier) {
        this._ensureLoaded();

        // example 'allele-sidebar .id-unclassified.enabled .nav-row .id-hgvsc'
        let all = browser.getText(`allele-sidebar ${identifier} .nav-row .id-hgvsc`);
        let allele_idx = 0;
        if (Array.isArray(all)) {
            allele_idx = all.findIndex(s => s === allele);
        }

        let allele_selector = '';
        if (allele_idx === -1) {
            throw Error(`Allele ${allele} not found among options ${all.join(',')}`);

        }
        allele_selector = `allele-sidebar ${identifier} .nav-row:nth-child(${allele_idx+1})`;
        browser.click(allele_selector);

        // Check that we changed active allele
        expect(browser.getClass(allele_selector).find(a => a === 'active')).toBeDefined();
    }

    selectUnclassifiedAllele(allele) {
        this._selectAllele(allele, '.id-unclassified.enabled')
    }

    selectClassifiedAllele(allele) {
        this._selectAllele(allele, '.id-classified.enabled')
    }

    isAlleleInUnclassified(allele) {
        let a = this.getUnclassifiedAlleles();
        if (Array.isArray(a)) {
            return a.find(al => al === allele) !== undefined;
        }
        return a === allele;
    }

    isAlleleInClassified(allele) {
        let a = this.getClassifiedAlleles();
        if (Array.isArray(a)) {
            return a.find(al => al === allele) !== undefined;
        }
        return a === allele;
    }


    open(page) {
        super.open('login');
    }

}

module.exports = AlleleSidebar