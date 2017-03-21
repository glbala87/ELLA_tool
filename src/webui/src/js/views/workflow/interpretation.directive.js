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
        genepanelName: '=',
        genepanelVersion: '=',
        analysis: '=?',
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
                AlleleFilter,
                CustomAnnotationModal) {

        this.clipboard = clipboard;
        this.toastr = toastr;
        this.navbar = Navbar;
        this.sidebar = Sidebar;
        this.alleleService = Allele;
        this.workflowResource = WorkflowResource;
        this.referenceResource = ReferenceResource;

        this.customAnnotationModal = CustomAnnotationModal;
        this.alleleFilter = AlleleFilter;

        this.showSidebar = 'showSidebar' in this ? this.showSidebar : true;

        $scope.$watch(
            () => this.interpretation.state,
            () => this.onInterpretationStateChange(),
            true // Deep watch
        );

        $scope.$watch(
            () => this.alleles,
            () => {
                this.setup();
                this.loadReferences();  // Reload references in case there are new alleles added
            }
        );


        this.config = Config.getConfig();

        this.references = [];  // Loaded references from backend

        this.allele_sidebar = {
            alleles: { // Holds data used by <allele-sidebar>
                unclassified: {
                    active: [],
                    inactive: []
                },
                classified: {
                    active: [],
                    inactive: []
                }
            },
            selected: null // Holds selected Allele from <allele-sidebar>
        };

        $scope.$watch(
            () => this.allele_sidebar.selected,
            () => this.navbar.setAllele(this.allele_sidebar.selected, this.analysis ? this.analysis.genepanel : null)
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

        if (!('analysis' in this.interpretation.state)) {
            this.interpretation.state.analysis = {};
        }
        if (!('properties' in this.interpretation.state.analysis)) {
            this.interpretation.state.analysis.properties = {
                tags: [],
                review_comment: ''
            }
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
        let alleles = {
            unclassified: {
                active: [],
                inactive: []
            },
            classified: {
                active: [],
                inactive: []
            }
        };

        let unclassified = this.filterClassifications(this.alleles);
        let classified = this.alleleFilter.invert(unclassified, this.alleles);

        // Mapping function for creating objects used by <allele-sidebar>
        let create_allele_obj = allele => {
            return {
                allele: allele,
                alleleState: this.getAlleleState(allele),
                togglable: this.selectedComponent.title === 'Report',  // When Report is select, we use checkable mode
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

        // Component name -> filter function for active alleles in this component
        let components = {
            'VarDB': alleles => this.alleleFilter.filterAlleleAssessment(alleles),
            'Report': alleles => {
                return alleles.filter(a => {
                    return Boolean(AlleleStateHelper.getClassification(a, this.getAlleleState(a)));
                });
            }
        };

        let comp_title = this.selectedComponent.title;
        if (comp_title in components) {
            let filtered_alleles = components[comp_title](unclassified);
            alleles.unclassified.active = filtered_alleles.map(create_allele_obj);
            alleles.unclassified.inactive = this.alleleFilter.invert(
                filtered_alleles,
                unclassified
            ).map(create_allele_obj);

            filtered_alleles = components[comp_title](classified);
            alleles.classified.active = filtered_alleles.map(create_allele_obj);
            alleles.classified.inactive = this.alleleFilter.invert(
                filtered_alleles,
                classified
            ).map(create_allele_obj);
        }
        else {  // Default -> all are active
            alleles.unclassified.active = unclassified.map(create_allele_obj);
            alleles.classified.active = classified.map(create_allele_obj);
        }

        // Sort data

        // Sort unclassified by (gene, hgvsc)
        let unclassified_sort = firstBy(a => a.allele.annotation.filtered[0].symbol)
                                .thenBy(a => a.allele.annotation.filtered[0].HGVSc_short);

        if (alleles.unclassified.active.length) {
            alleles.unclassified.active.sort(unclassified_sort);
        }
        if (alleles.unclassified.inactive.length) {
            alleles.unclassified.inactive.sort(unclassified_sort);
        }

        // Sort classified by (classification, gene, hgvsc)
        let classified_sort = firstBy(a => {
                let classification = AlleleStateHelper.getClassification(a.allele, this.getAlleleState(a.allele));
               return this.config.classification.options.findIndex(o => o.value === classification);
            }, -1)
            .thenBy(a => a.allele.annotation.filtered[0].symbol)
            .thenBy(a => a.allele.annotation.filtered[0].HGVSc_short);

        if (alleles.classified.active.length) {
            alleles.classified.active.sort(classified_sort);
        }
        if (alleles.classified.inactive.length) {
            alleles.classified.inactive.sort(classified_sort);
        }

        this.allele_sidebar.alleles = alleles;
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
        return this.allele_sidebar.alleles.unclassified.active.length > 0 ||
               this.allele_sidebar.alleles.classified.active.length > 0;
    }

    /**
     * Calls updateAlleleSidebar and checks that the currently selected allele
     * is among the unclassified, active options. If not, select the first one.
     */

    onComponentChange() {
        this.updateAlleleSidebar();

        // Report component use toggle system instead of single selection
        if (this.selectedComponent.title === 'Report') {
            this.allele_sidebar.selected = null;
            return;
        };

        if (this.allele_sidebar.alleles.unclassified.active.length) {
            this.allele_sidebar.selected = this.allele_sidebar.alleles.unclassified.active[0].allele;
        }
        else if (this.allele_sidebar.alleles.classified.active.length) {
            this.allele_sidebar.selected = this.allele_sidebar.alleles.classified.active[0].allele;
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
    filterClassifications(alleles) {
        if (!('allele' in this.interpretation.state)) {
            return alleles;
        };

        return alleles.filter(al => {
            let allele_state = this.getAlleleState(al);
            if (allele_state !== undefined) {
                return AlleleStateHelper.getClassification(al, allele_state) === null;
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
        this.references = [];
        let reference_ids = []
        let pubmed_ids = []
        for (let id of ids) {
            if (id.id !== undefined) {
                reference_ids.push(id.id)
            } else if (id.pubmed_id !== undefined) {
                pubmed_ids.push(id.pubmed_id)
            }
        }

        this.referenceResource.getByIds(reference_ids).then(references => {
            this.references = this.references.concat(references);
        });
        this.referenceResource.getByPubMedIds(pubmed_ids).then(references => {
            this.references = this.references.concat(references);
        });
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


