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
        comments: '=',  // Array of [{model: string, placeholder: string}, ...]
        section: '=',  // Section to display using <allelesectionboxcontent>
        updateText: '@?',
        onUpdate: '&?',  // On-update callback function (should refresh allele)
        onSetClass: '&?',  // Callback function when clicking 'Set' button for setting class
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
    'Analysis',
    'Interpretation',
    'clipboard',
    'toastr'
)
export class AlleleSectionBoxController {


    constructor(rootScope,
                Config,
                Allele,
                CustomAnnotationModal,
                Analysis,
                Interpretation,
                clipboard,
                toastr) {
        this.config = Config.getConfig();
        this.alleleService = Allele;
        this.customAnnotationModal = CustomAnnotationModal;
        this.interpretationService = Interpretation;
        this.analysisService = Analysis;
        this.clipboard = clipboard;
        this.toastr = toastr;

        this.selected_class = null; // Stores selected class in dropdown
        this.calculated_config = null; // calculated at request.

        this.classificationOptions = this.config.classification.options;

        this.sectionOptions = {};  // {'alleleinfo-something': {collapsed: true, ...}}

        this.setupSectionOptions();

        // This is a hack around the fact
        // that <sectionbox> contains the toggle for
        // the collapse action, so we need to watch
        // it's collapsed state and act on that.
        rootScope.$watch(
            () => this.section.options.collapsed,
            () => this.toggleCollapse()
        );
    }


    /**
     * Creates option objects for the <contentbox> es
     * used as part of provided section.
     */
    setupSectionOptions() {
        this.sectionOptions = {};
        for (let s of this.section.content) {
            this.sectionOptions[s.tag] = {
                collapsed: false,
                url: '', // Will be set by alleleinfo itself
                title: '', // Likewise
                disabled: false // Likewise
            }
        }
    }

    /**
     * Toggles collapse state on all child <contentbox>es through the
     * section options.
     */
    toggleCollapse() {
        for (let s of this.section.content) {
            this.sectionOptions[s.tag].collapsed = this.section.options.collapsed;
        }
    }


    getInheritanceCodes(geneSymbol) {
        return this.genepanel.getInheritanceCodes(geneSymbol);
    }

    phenotypesBy(geneSymbol) {
        return this.genepanel.phenotypesBy(geneSymbol);
    }

    getGenepanelValues(geneSymbol) {
        //  Cache calculation; assumes this card is associated with only one gene symbol
        if (! this.calculated_config) {
            this.calculated_config = this.genepanel.calculateGenepanelConfig(geneSymbol, this.config.variant_criteria.genepanel_config);
        }
        return this.calculated_config;
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

    updateClassification() {
        AlleleStateHelper.updateClassification(this.alleleState, this.selected_class);

        if (this.onSetClass) {
            this.onSetClass({allele: this.allele});
        }
    }

    toggleClass2() {
        AlleleStateHelper.toggleClass2(this.alleleState);

        if (this.onSkip) {
            this.onSkip();
        }
    }

    toggleTechnical() {
        AlleleStateHelper.toggleTechnical(this.alleleState);

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
