var Page = require('./page')

class CustomAnnotationModal extends Page {
    get externalAnnotationSelect() {
        return $('.id-custom-annotation-modal .id-annotation-select')
    }
    get predictionBtnSet() {
        return $('.id-custom-annotation-modal .id-annotation-select')
    }
    get saveBtn() {
        return $('.id-custom-annotation-modal .id-save')
    }
    get cancelBtn() {
        return $('.id-custom-annotation-modal .id-cancel')
    }
    get pubMedBtn() {
        return $('.id-referenceMode-PubMed')
    }
    get addReferenceBtn() {
        return $('.id-custom-annotation-modal .id-add-reference-button')
    }
    get xmlInput() {
        return $('.id-custom-annotation-modal .id-reference-xml')
    }
    get xmlInputEditor() {
        return $('.id-custom-annotation-modal .id-reference-xml textarea')
    }

    /**
     * Sets an external annotation database to some value.
     * (uses <select>)
     * @param {*} idx  Index in the list of available external databases
     * @param {*} dropdown_option_text  Text of dropdown option
     */
    setExternalAnnotation(idx, dropdown_option_text) {
        if (idx === 2) {
            throw Error(
                'idx === 2 is broken for some obscure reason, it selects 1 instead...every other idx should work fine.'
            )
        }
        let dropdown = $(
            `.id-custom-annotation-modal article:nth-child(${idx}) .id-annotation-select`
        )
        dropdown.selectByVisibleText(dropdown_option_text)
    }

    /**
     * Sets prediction annotation to some value.
     * (uses <bttn-set>)
     * @param {*} idx  Index in the list of available prediction options
     * @param {*} button_idx  Index of button-group button
     */
    setPredictionAnnotation(idx, button_idx) {
        let bttn_set = $(
            `.id-custom-annotation-modal article:nth-child(${idx}) .id-annotation-bttn-set label:nth-child(${button_idx})`
        )
        bttn_set.click()
    }

    setText(element, text) {
        browser.selectorExecute(
            element.selector,
            function(matchingElements, msg) {
                let e = matchingElements[0]
                e.value = msg
                // make Angular aware of the change:
                e.dispatchEvent(new Event('input', { bubbles: true })) //Works
            },
            text
        )
    }

    referenceList() {
        let selector = '.id-custom-annotation-modal .id-references-list article'
        return $$(selector)
    }

    waitForClose() {
        $('.id-custom-annotation-modal').waitForExist(10000, true)
    }
}

module.exports = CustomAnnotationModal
