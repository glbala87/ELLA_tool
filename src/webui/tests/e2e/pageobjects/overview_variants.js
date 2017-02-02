var Page = require('./page');

const SELECTOR_FINISHED = '.id-variants-finished';
const SELECTOR_PENDING = '.id-variants-pending'; // no assessment
const SELECTOR_REVIEW = '.id-variants-review';
const SELECTOR_YOURS = '.id-variants-yours';
const SELECTOR_OTHERS = '.id-variants-others';


const SELECTOR_VARIANT_NAME = ".id-variant-name";

const SECTION_EXPAND_SELECTOR  = " header .sb-title-container";

class VariantSelection extends Page {

    get variantList() { return browser.element('allele-list') }
    get yoursSection() { return browser.element(SELECTOR_YOURS) };
    get othersSection() { return browser.element(SELECTOR_OTHERS) };
    get pendingSection() { return browser.element(SELECTOR_PENDING) }
    get reviewSection() { return browser.element(SELECTOR_REVIEW) }
    get finishedSection() { return browser.element(SELECTOR_FINISHED) }


    expandPendingSection() {
        this._expandSection(SELECTOR_PENDING);
    }

    expandReviewSection() {
        this._expandSection(SELECTOR_REVIEW);
    }

    _expandSection(sectionSelector) {
        this.open();
        browser.waitForExist(sectionSelector);
        browser.click(sectionSelector + SECTION_EXPAND_SELECTOR);
    }

    selectItemInSection(number, sectionSelector) {
        this.open();
        // expand box:
        browser.waitForExist(sectionSelector);
        browser.click(sectionSelector + SECTION_EXPAND_SELECTOR);
        let selector = `${sectionSelector} .id-variant:nth-child(${number})`;
        // console.log('Going to click selector:' + selector);
        browser.waitForExist(selector);
        browser.click(selector);
        let element = browser.element(selector);
        browser.waitForExist('allele-list', 5000, true);
        return element;
    }

    selectFinished(number) {
        this.selectItemInSection(number, SELECTOR_FINISHED);
    }

    selectPending(number, name) {
        let wrapper = this.selectItemInSection(number, SELECTOR_PENDING);
        // attempt to validate the chosen element matches the name:
        // This fails with a Cannot read property 'ELEMENT' of null
        // let analysisNameElement = wrapper.element(SELECTOR_ANALYSIS_NAME);
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

    selectReview(number) {
        this.selectItemInSection(number, SELECTOR_REVIEW);
    }

    selectYours(number) {
        this.selectItemInSection(number, SELECTOR_YOURS);
    }

    selectOthers(number) {
        this.selectItemInSection(number, SELECTOR_OTHERS);
    }

    open() {
        super.open('overview/variants');
    }

    selectTopPending() {
        this.selectPending(1);
    }

    selectTopReview() {
        this.selectReview(1);
    }

    getReviewComment() {
        let selector = `${SELECTOR_REVIEW} .allele-extras .id-allele-comment`;
        return browser.getText(selector)
    }

}

module.exports = VariantSelection;