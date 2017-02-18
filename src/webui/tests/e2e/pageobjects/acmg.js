var Page = require('./page');


const SELECTOR_TOP = '.id-acmg-container';
const SELECTOR_SUGGESTED = '.id-acmg-suggested';
const SELECTOR_SUGGESTED_REQ = '.id-acmg-suggested-req';
const SELECTOR_INCLUDE = '.id-acmg-included';
const SELECTOR_SHOW_HIDE = '.id-acmg-show-hide-req';

class Acmg extends Page {


    // get commentElement() { return browser.element('.workflow-options input.id-review-comment'); }

    get showHideBtn() { return browser.element(`${SELECTOR_TOP} ${SELECTOR_SHOW_HIDE}`);}
    get suggestedElement() { return browser.element(`${SELECTOR_TOP} ${SELECTOR_SUGGESTED}`);}
    get suggestedReqElement() { return browser.element(`${SELECTOR_TOP} ${SELECTOR_SUGGESTED_REQ}`);}



    hasShowHideButton() {
        return browser.isExisting(`${SELECTOR_SHOW_HIDE}`);
    }

    // getReferences() {
    //     return browser.elements('allele-sectionbox .id-references-box article');
    // }

}

module.exports = Acmg;
