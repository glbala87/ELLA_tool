/* jshint esnext: true */

import {Directive, Inject} from '../../ng-decorators';
import {AlleleStateHelper} from '../../model/allelestatehelper';

@Directive({
    selector: 'allele-sectionbox',
    templateUrl: 'ngtmpl/allelesectionbox.ngtmpl.html',
    scope: {
        header: '=',
        genepanel: '=',
        allele: '=',
        references: '=',
        alleleState: '=',
        alleleUserState: '=',
        analysis: '=?', // Used for IGV (optional)
        comments: '=',  // Array of [{model: string, placeholder: string}, ...]
        section: '=',  // Section to display using <allelesectionboxcontent>
        updateText: '@?',
        onUpdate: '&?',  // On-update callback function (should refresh allele)
        onChangeClass: '&?',  // Callback function when changing class (dropdown)
        onSkip: '&?', // Callback function when clicking 'Skip' button. Enables skip button.
        controls: '=',
        // possible controls: {
        //   toggle_technical: bool,
        //   toggle_class2: bool,
        //   skip_next: bool,
        //   checked: bool,
        //   classification: bool,
        //   vardb: bool,
        //   custom_prediction: bool,
        //   custom_external: bool
        //}
        //
    }

})
@Inject(
    '$rootScope',
    'Config',
    'Allele',
    'CustomAnnotationModal',
    'IgvModal',
    'Analysis',
    'clipboard',
    'toastr'
)
export class AlleleSectionBoxController {


    constructor(rootScope,
                Config,
                Allele,
                CustomAnnotationModal,
                IgvModal,
                Analysis,
                clipboard,
                toastr) {
        this.config = Config.getConfig();
        this.alleleService = Allele;
        this.customAnnotationModal = CustomAnnotationModal;
        this.igvModal = IgvModal;
        this.analysisService = Analysis;
        this.clipboard = clipboard;
        this.toastr = toastr;

        this.selected_class = null; // Stores selected class in dropdown
        this.calculated_config = null; // calculated at request.

        this.classificationOptions = [{name: 'Unclassified', value: null}].concat(this.config.classification.options);

    }

    /**
     * Whether the card is editable or not. If reusing alleleassessment, user cannot edit the card.
     * Defaults to true if no data.
     * @return {Boolean}
     */
    isEditable() {
        return !this.isAlleleAssessmentReused();
    }

    getClassification() {
        return AlleleStateHelper.getClassification(this.allele, this.alleleState);
    }

    getAlleleAssessment() {
        return AlleleStateHelper.getAlleleAssessment(this.allele, this.alleleState);
    }

    /**
     * If the allele has an existing alleleassessment,
     * check whether it's outdated.
     * @return {Boolean}
     */
    isAlleleAssessmentOutdated() {
        return AlleleStateHelper.isAlleleAssessmentOutdated(this.allele, this.config);
    }

    getCardColor() {
        if (this.isAlleleAssessmentReused()) {
                return 'yellow';
        }
        return 'blue';
    }

    hasExistingAlleleAssessment() {
        return this.allele.allele_assessment;
    }

    isAlleleAssessmentReused() {
        return AlleleStateHelper.isAlleleAssessmentReused(this.alleleState);
    }

    ///////////////
    /// Controls
    ///////////////

    showIgv() {
        this.igvModal.show(this.analysis, this.allele);
    }

    showCustomAnnotationModal(category) {
        let title = category === 'external' ? 'ADD EXTERNAL ANNOTATION' : 'ADD PREDICTION ANNOTATION';
        this.customAnnotationModal.show(title, [this.allele], category).then(result => {
            if (result) {
                if (this.onUpdate) {
                    this.onUpdate();
                }
            }
        });
    }

    showAddReferenceModal() {
        let title = 'ADD REFERENCES';
        this.customAnnotationModal.show(title, [this.allele], 'references').then(result => {
            if (result) {
                if (this.onUpdate) {
                    this.onUpdate();
                }
            }
        });
    }

    changeClassification() {

        if (this.onChangeClass) {
            this.onChangeClass({allele: this.allele});
        }
    }

    setClass1() {
        this.alleleState.alleleassessment.classification = '1';

        if (this.onSkip) {
            this.onSkip();
        }
    }

    setClass2() {
        this.alleleState.alleleassessment.classification = '2';

        if (this.onSkip) {
            this.onSkip();
        }
    }

    setTechnical() {
        this.alleleState.alleleassessment.classification = 'T';

        if (this.onSkip) {
            this.onSkip();
        }
    }

    toggleReuseAlleleAssessment() {
        if (AlleleStateHelper.toggleReuseAlleleAssessment(this.allele, this.alleleState, this.config)) {
            if (this.onSetClass) {
                this.onSetClass({allele: this.allele});
            }
        };
    }

    getUpdateText() {
        return this.updateText !== undefined ? this.updateText : 'Set class';
    }

    copyAlamut() {
        this.clipboard.copyText(this.allele.formatAlamut());
        this.toastr.info('Copied text to clipboard', null, {timeOut: 1000});
    }

}
