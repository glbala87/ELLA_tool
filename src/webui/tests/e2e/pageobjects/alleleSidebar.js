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

    getSelectedAlleleClassification() {
        return browser.getText('allele-sidebar .enabled .nav-row.active .id-classification');
    }

    _selectAllele(allele, identifier) {
        this._ensureLoaded()

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