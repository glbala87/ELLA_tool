/* jshint esnext: true */

import {Directive, Inject} from '../../ng-decorators';
import {AlleleStateHelper} from '../../model/allelestatehelper';


/**
 * This is the main entry to the interpretation of a single-sampled analysis (as opposed to a trio sample).
 *
 * The main data stores are:
 * - this.alleles The variants/alleles and annotations for those. Fetched from backend upon page load or when
 * significant changes happen
 * - this.interpretation.state: stores the result of various user activities, like variant assessment.
 * More specifically the this.interpretation.state.allele is an array of with state for each variant/allele
 *
 */

// TODO: add logic to include/exclude controls in read-only mode

@Directive({
    selector: 'interpretation',
    templateUrl: 'ngtmpl/interpretation.ngtmpl.html',
    scope: {
        interpretation: '=',
        components: '=',
        selectedComponent: '=',
        genepanel: '=',
        updateAlleles: '&',
        alleles: '=',
        showSidebar: '=?',
        readOnly: '='
    }
})
@Inject('$scope',
        'clipboard',
        'toastr',
        'Navbar',
        'Sidebar',
        'Config',
        'Allele',
        'WorkflowResource',
        'ReferenceResource',
        'AttachmentResource',
        'AlleleFilter',
        'CustomAnnotationModal')
export class InterpretationController {

    constructor($scope,
                clipboard,
                toastr,
                Navbar,
                Sidebar,
                Config,
                Allele,
                WorkflowResource,
                ReferenceResource,
                AttachmentResource,
                AlleleFilter,
                CustomAnnotationModal) {

        this.clipboard = clipboard;
        this.toastr = toastr;
        this.navbar = Navbar;
        this.sidebar = Sidebar;
        this.alleleService = Allele;
        this.workflowResource = WorkflowResource;
        this.referenceResource = ReferenceResource;
        this.attachmentResource = AttachmentResource;

        this.customAnnotationModal = CustomAnnotationModal;
        this.alleleFilter = AlleleFilter;

        this.showSidebar = 'showSidebar' in this ? this.showSidebar : true;

        $scope.$watch(
            () => this.interpretation.state,
            () => this.onInterpretationStateChange(),
            true // Deep watch
        );

        $scope.$watchCollection(
            () => this.getAttachmentIds(),
            () => this.loadAttachments(this.getAttachmentIds()),
        );

        $scope.$watch(
            () => this.alleles,
            () => {
                this.setup();
                this.loadReferences();  // Reload references in case there are new alleles added
            }
        );


        this.config = Config.getConfig();

        this.references = null;  // Loaded references from backend. null = not loaded.
        this.attachments = {};

        this.allele_sidebar = {
            alleles: { // Holds data used by <allele-sidebar>
                unclassified: [],
                classified: []
            },
            selected: null // Holds selected Allele from <allele-sidebar>
        };

        $scope.$watch(
            () => this.allele_sidebar.selected,
            () => this.navbar.setAllele(this.allele_sidebar.selected, this.genepanel)
        );

        $scope.$watch(
            () => this.interpretation,
            () => this.setup()
        );

        $scope.$watch(
            () => this.selectedComponent,
            () => this.onComponentChange()
        );

    }




    setup() {

        // Create state objects
        if (!('allele' in this.interpretation.state)) {
            this.interpretation.state.allele = {};
        }

        this.setupSidebar();

        this.autoReuseExistingAssessments();
        this.onInterpretationStateChange();

    }

    setupSidebar() {
        this.sidebar.replaceItems(this.components);
    }

    /**
     * Mark all existing alleleassessments as being reused
     * as convenience for the user.
     */
    autoReuseExistingAssessments() {
        for (let allele of this.alleles) {

            let changed = AlleleStateHelper.autoReuseExistingAssessment(allele, this.getAlleleState(allele), this.config);
            if (changed) {
                // Recheck allele whether allele should now be added to/removed from report.
                AlleleStateHelper.checkAddRemoveAlleleToReport(allele, this.getAlleleState(allele), this.config);
            }
        }
    }

    /**
     * Called by <allele-sectionbox> whenever an allele needs
     * refreshing from backend (data has changed)
     */
    onUpdate() {
        this.updateAlleles();
    }

    /**
     * Called by <allele-sectionbox> whenever a class is changed.
     */
    onChangeClass(allele) {
        AlleleStateHelper.checkAddRemoveAlleleToReport(allele, this.getAlleleState(allele), this.config);
    }

    getSidebarSelected() {
        return this.selectedComponent.title;
    }

    /**
     * Called when interpretations state changes.
     * Updates AlleleSidebar and alleles to be included in report.
     */
    onInterpretationStateChange() {
        // Update report alleles
        let report_component = this.getComponent('Report');
        if (report_component) {
            report_component.alleles = this.alleles.filter(a => {
                let state = this.getAlleleState(a);
                if ('report' in state &&
                    'included' in state.report) {
                    return state.report.included
                }
                return false;
            });
        }
        this.updateAlleleSidebar();
    }
    /**
     * Updates the structure used by <allele-sidebar>.
     * FIXME: updateAlleleSidebar is called 5 times on page load: through $watch, $watchCollection, setup(), $watch, $watchCollection
     */
    updateAlleleSidebar() {

        // Mapping function for creating objects used by <allele-sidebar>
        let create_allele_obj = allele => {
            return {
                allele: allele,
                alleleState: this.getAlleleState(allele),
                checkable: this.selectedComponent.title === 'Report',
                togglable: this.selectedComponent.title === 'Report' && Boolean(AlleleStateHelper.getClassification(allele, this.getAlleleState(allele))),  // When Report is select, we use checkable mode
                isToggled: () => {
                    let state = this.getAlleleState(allele);
                    if (!('report' in state)) {
                        state.report = {
                            included: false
                        }
                    }
                    if (!('included') in state.report) {
                        state.report.included = false;
                    }
                    return state.report.included;
                },
                toggle: () => { // variant clicked in sidebar
                    if (this.readOnly) { // don't allow changing reports
                        return;
                    }

                    let state = this.getAlleleState(allele);
                    if (!('report' in state)) {
                        state.report = {
                            included: false
                        }
                    }
                    if (!('included') in state.report) {
                        state.report.included = false;
                    }
                    state.report.included = !state.report.included;
                }
            }
        };

        // Populate the input to alleleSidebar, separating classified and unclassified alleles
        let unclassified = this.findUnclassified(this.alleles);
        let grouped_alleles = {
            unclassified: unclassified.map(create_allele_obj),
            classified: this.alleleFilter.invert(unclassified, this.alleles).map(create_allele_obj)
        };

        // Sort data
        // Sort unclassified by (gene, hgvsc)
        let unclassified_sort = firstBy(a => this.genepanel.getDisplayInheritance(a.allele.annotation.filtered[0].symbol))
                                .thenBy(a => a.allele.annotation.filtered[0].symbol)
                                .thenBy(a => a.allele.annotation.filtered[0].HGVSc_short);

        if (grouped_alleles.unclassified.length) {
            grouped_alleles.unclassified.sort(unclassified_sort);
        }

        let classified_sort = firstBy(a => {
                let classification = AlleleStateHelper.getClassification(a.allele, this.getAlleleState(a.allele));
               return this.config.classification.options.findIndex(o => o.value === classification);
            }, -1)
            .thenBy(a => this.genepanel.getDisplayInheritance(a.allele.annotation.filtered[0].symbol))
            .thenBy(a => a.allele.annotation.filtered[0].symbol)
            .thenBy(a => a.allele.annotation.filtered[0].HGVSc_short);

        if (grouped_alleles.classified.length) {
            grouped_alleles.classified.sort(classified_sort);
        }

        this.allele_sidebar.alleles = grouped_alleles;
        // Reassign selected allele in case the allele data has changed
        if (this.allele_sidebar.selected) {
            let selected = this.alleles.find(a => a.id === this.allele_sidebar.selected.id);
            if (selected) { // could be null if selected was an excluded allele manually included by user
                this.allele_sidebar.selected = selected;
            } else {
                this.allele_sidebar.selected = this.alleles[0];
            }
        }
    }

    getComponent(component_name) {
        return this.components.find(c => c.title === component_name);
    }

    hasResults() {
        return this.allele_sidebar.alleles.unclassified.length > 0 ||
               this.allele_sidebar.alleles.classified.length > 0;
    }

    /**
     * Calls updateAlleleSidebar and checks that the currently selected allele
     * is among the unclassified options. If not, select the first one.
     */

    onComponentChange() {
        this.updateAlleleSidebar();

        // Report component use toggle system instead of single selection
        if (this.selectedComponent.title === 'Report') {
            this.allele_sidebar.selected = null;
            return;
        };

        if (this.allele_sidebar.alleles.unclassified.length) {
            this.allele_sidebar.selected = this.allele_sidebar.alleles.unclassified[0].allele;
        }
        else if (this.allele_sidebar.alleles.classified.length) {
            this.allele_sidebar.selected = this.allele_sidebar.alleles.classified[0].allele;
        }
        else {
            this.allele_sidebar.selected = null;
        }
    }


    /**
     * Filters away all alleles that have a classification set
     * in the interpretation state.
     * @param  {Array(Allele)} alleles to filter
     * @return {Array} Filtered array of Alleles
     */
    findUnclassified(alleles) {
        if (!('allele' in this.interpretation.state)) {
            return alleles;
        };

        return alleles.filter(al => {
            let allele_state = this.getAlleleState(al);
            if (allele_state !== undefined) {
                return !Boolean(AlleleStateHelper.getClassification(al, allele_state));
            }
            return true;
        });
    }

    /**
     * Retrives combined PubMed IDs for all alles.
     * @return {Array} Array of ids.
     */
    _getReferenceIds(alleles) {
        let ids = [];
        for (let allele of alleles) {
            Array.prototype.push.apply(ids, allele.getReferenceIds());
        }
        return ids;
    }

    loadReferences() {
        let ids = this._getReferenceIds(this.alleles);
        // Load references for our alleles from backend

        // Search first for references by reference id, then by pubmed id where reference id is not defined
        this.references = null;
        let reference_ids = []
        let pubmed_ids = []
        for (let id of ids) {
            if (id.id !== undefined) {
                reference_ids.push(id.id)
            } else if (id.pubmed_id !== undefined) {
                pubmed_ids.push(id.pubmed_id)
            }
        }
        // Load references from backend in two requests
        if (reference_ids.length || pubmed_ids.length) {
            let ref_by_id = this.referenceResource.getByIds(reference_ids);
            let ref_by_pmid = this.referenceResource.getByPubMedIds(pubmed_ids);
            Promise.all([ref_by_id, ref_by_pmid]).then(args => {
                let [ref_id, ref_pmid] = args;
                this.references = ref_id.concat(ref_pmid);
            });
        }
        else {
            this.references = [];
        }
    }

    /**
     * Retrieves attachment ids for all allele states
     * @return {Array} Array of ids.
     */
    getAttachmentIds() {
        let attachment_ids = []
        for (let allele_id in this.interpretation.state.allele) {
            if ("alleleassessment" in this.interpretation.state.allele[allele_id]) {
                attachment_ids = attachment_ids.concat(this.interpretation.state.allele[allele_id].alleleassessment.attachment_ids)
            }
        }

        for (let allele of this.alleles) {
            if ("allele_assessment" in allele) {
                attachment_ids = attachment_ids.concat(allele.allele_assessment.attachment_ids)
            }
        }
        attachment_ids = [... new Set(attachment_ids)]

        return attachment_ids;
    }

    /**
     * Loads attachments from backend
     * @param {Array} attachment_ids
     */
    loadAttachments(attachment_ids) {
        let attachments = {};
        this.attachmentResource.getByIds(attachment_ids).then((a) => {
            for (let atchmt of a) {
                attachments[atchmt.id] = atchmt;
            }
            this.attachments = attachments;
        })
    }


    /**
     * Returns allelestate object for the provided allele.
     * If the allelestate doesn't exist, create it first.
     * @param  {Allele} allele
     * @return {Object} allele state for given allele
     */
    getAlleleState(allele) {
        if (!('allele' in this.interpretation.state)) {
            this.interpretation.state.allele = {};
        }
        if (!(allele.id in this.interpretation.state.allele)) {
            let allele_state = {
                allele_id: allele.id,
            };
            this.interpretation.state.allele[allele.id] = allele_state;
        }
        return this.interpretation.state.allele[allele.id];
    }

    getAlleleUserState(allele) {
        if (!('allele' in this.interpretation.user_state)) {
            this.interpretation.user_state.allele = {};
        }
        if (!(allele.id in this.interpretation.user_state.allele)) {
            let allele_state = {
                allele_id: allele.id,
                showExcludedReferences: false,
            };
            this.interpretation.user_state.allele[allele.id] = allele_state;
        }
        return this.interpretation.user_state.allele[allele.id];
    }


}


