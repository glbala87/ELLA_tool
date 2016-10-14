var Page = require('./page')


class AlleleSidebar extends Page {

    _ensureLoaded() {
        browser.waitForExist('allele-sidebar .nav-row');
    }

    _getUnclassifiedAlleleIndex(allele) {
        let all = browser.getText('allele-sidebar .id-unclassified.enabled .nav-row .variant span');
        return all.findIndex(s => allele);
    }

    getUnclassifiedAlleles() {
        this._ensureLoaded();
        return browser.getText('allele-sidebar .id-unclassified.enabled .nav-row .variant span');
    }

    getClassifiedAlleles() {
        this._ensureLoaded();
        return browser.getText('allele-sidebar .id-classified.enabled .nav-row .variant span');
    }

    getSelectedAllele() {
        this._ensureLoaded();
        return browser.getText('allele-sidebar .enabled .nav-row.active .variant span');
    }

    selectAllele(allele) {
        this._ensureLoaded()

        let selected_idx = this._getUnclassifiedAlleleIndex(this.getSelectedAllele())
        if (selected_idx === -1) {
            throw Error(`Allele ${allele} not found among options ${all.join(',')}`);
        }

        let allele_selector = `allele-sidebar .enabled .nav-row:nth-child(${selected_idx+1})`;
        browser.click(allele_selector);

        // Check that we changed active allele
        expect(browser.getClass(allele_selector).find(a => a === 'active')).toBeDefined();
    }

    selectNextAllele() {
        this._ensureLoaded();
        let all = browser.getText('allele-sidebar .id-unclassified.enabled .nav-row .variant span');
        let selected_allele = this.getSelectedAllele();
        let selected_idx = all.findIndex(s => selected_allele);

        this.selectAllele(all[selected_idx+1]);
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