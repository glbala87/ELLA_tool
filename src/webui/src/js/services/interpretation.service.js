/* jshint esnext: true */

/**
 * Interpretation service to act as state manager for the interpretation object and interpretation history
 * during a workflow. Previously part of WorkflowAllele and WorkflowAnalysis directives. Separated here as
 * a service to avoid duplicate code, and to allow for more flexibility, specifically that we can access
 * and modify the interpretation object from different controllers.
 *
 * There are some minor differences between allele and analysis workflow. Most notably is the lack of a
 * default interpretation object for allele. On import of analysis, an interpretation object is created
 * with status NOT STARTED. This is not the case for alleles. To account for this, we create a dummy
 * interpretation object that we use for alleles without an existing interpretation object.
 */

import { Service, Inject } from '../ng-decorators'
import { STATUS_ONGOING, STATUS_NOT_STARTED } from '../model/interpretation'
import { deepCopy } from '../util'

@Service({
    serviceName: 'Interpretation'
})
@Inject('$rootScope', 'WorkflowResource', 'Workflow', 'Allele', 'AnalysisResource', 'User')
class InterpretationService {
    constructor($rootScope, WorkflowResource, Workflow, Allele, AnalysisResource, User) {
        this.rootScope = $rootScope
        this.workflowResource = WorkflowResource
        this.workflowService = Workflow
        this.alleleService = Allele
        this.analysisResource = AnalysisResource
        this.user = User

        this.reset()
        this._setWatchers()
    }

    /**
     * Watchers on scope should generally not be part of a service, but keep it here, as they are very
     * specific to the interpretation state.
     */

    _setWatchers() {
        // Set interpretation dirty when changes have been made to the state
        let watchStateFn = () => {
            if (this.isOngoing() && this.getSelected().state) {
                return this.getSelected().state
            }
        }

        let watchUserStateFn = () => {
            if (this.isOngoing() && this.getSelected().user_state) {
                return this.getSelected().user_state
            }
        }

        this.rootScope.$watch(
            watchStateFn,
            (n, o) => {
                // If no old object, we're on the first iteration
                // -> don't set dirty
                if (this.getSelected() && o) {
                    this.getSelected().setDirty()
                }
            },
            true
        ) // true -> Deep watch

        this.rootScope.$watch(
            watchUserStateFn,
            (n, o) => {
                if (this.getSelected() && o) {
                    this.getSelected().setDirty()
                }
            },
            true
        ) // true -> Deep watch

        /* Reset interpretations whenever we navigate away
         * NOTE: This should ideally not be part of the service. The idea is that an interpretation is
         * specific to a single view. Might need to be removed or moved to the separate views.
         */
        this.rootScope.$on('$locationChangeSuccess', this.reset())
    }

    reset() {
        this.selected_interpretation = null // Holds displayed interpretation
        this.selected_interpretation_alleles = null // Loaded allele for current interpretation (annotation etc data can change based on interpretation snapshot)
        this.selected_interpretation_genepanel = null // Loaded genepanel for current interpretation (used in navbar)
        this.interpretations = [] // Holds interpretations from backend
        this.history_interpretations = [] // Filtered interpretations, containing only the finished ones. Used in dropdown

        this.type = null
        this.id = null
        this.genepanel_name = null
        this.genepanel_version = null
        //
        // this.genepanel_options = null;
        // this.genepanel_options_selected = null;

        this.analysis = null

        // Dummy data for letting the user browse the view before starting interpretation. Never stored!
        // Only used for variants, as variant interpretation is not available by default in the backend
        // Analysis interpretation objects are created on import
        this.dummy_interpretation = {
            genepanel_name: null,
            genepanel_version: null,
            dirty: false,
            state: {},
            user_state: {},
            status: STATUS_NOT_STARTED
        }

        this.dummy_interpretation.setDirty = () => {
            this.dummy_interpretation.dirty = true
        }

        this.isViewReady = false // For hiding view until we've checked whether we have interpretations
    }

    /**
     * Load analysis (if applicable), interpretations, alleles, and genepanel (in that order)
     *
     * @param type Type of interpretation (allele or analysis)
     * @param id Id of allele or analysis
     * @param genepanel_name Genepanel name (only applicable for alleles, for analyses it's fetched from interpretation object)
     * @param genepanel_version Genepanel version (only applicable for alleles, for analyses it's fetched from interpretation object)
     * @returns {Promise.<TResult>|*}
     */
    load(type, id, genepanel_name, genepanel_version) {
        if (type === 'analysis') {
            this.loadAnalysis(id)
        }
        return this._loadInterpretations(type, id, genepanel_name, genepanel_version).then(() => {
            return this.loadAlleles(true).then(() => {
                return this.loadGenepanel()
            })
        })
    }

    /**
     * Loads interpretations from backend and sets:
     * - selected_interpretation
     * - history_interpretations
     * - interpretations
     */
    _loadInterpretations(type, id, genepanel_name, genepanel_version) {
        this.reset()
        this.type = type
        this.id = id
        this.genepanel_name = genepanel_name
        this.genepanel_version = genepanel_version

        if (this.type === 'allele') {
            // Set dummy interpretation allele ids for allele interpretations
            // Analysis interpretations should always be present in the database, this is not the case for allele interpretations
            this.dummy_interpretation.allele_ids = [this.id]
            this.dummy_interpretation.genepanel_name = genepanel_name
            this.dummy_interpretation.genepanel_version = genepanel_version
        }
        return this.workflowResource.getInterpretations(type, id).then((interpretations) => {
            this.interpretations = interpretations
            let done_interpretations = this.interpretations.filter((i) => i.status === 'Done')
            let last_interpretation = this.interpretations[this.interpretations.length - 1]
            // If an interpretation is Ongoing, we assign it directly
            if (last_interpretation && last_interpretation.status === 'Ongoing') {
                this.selected_interpretation = last_interpretation
                this.selected_interpretation.current = true
                this.history_interpretations = done_interpretations
            } else if (done_interpretations.length) {
                // Otherwise, make a copy of the last historical one to act as "current" entry.
                // Current means get latest allele data (instead of historical)
                // We make a copy, to prevent the state of the original to be modified
                let current_entry_copy = deepCopy(
                    done_interpretations[done_interpretations.length - 1]
                )
                current_entry_copy.current = true
                this.selected_interpretation = current_entry_copy
                this.history_interpretations = done_interpretations.concat([current_entry_copy])
            } else {
                // If we have no history, set selected to last interpretation (undefined if no last_interpretation)
                this.selected_interpretation = last_interpretation
                this.history_interpretations = []
            }
            // this.interpretations_loaded = true;
            console.log('(Re)Loaded ' + interpretations.length + ' interpretations')
            console.log('Setting selected interpretation:', this.selected_interpretation)
            this.interpretations_loaded = true
        })
    }

    /**
     * Load alleles from interpretation if defined. If not defined, and interpretation type is 'allele',
     * load allele directly from id
     */
    loadAlleles(setViewReady) {
        if (setViewReady) this.isViewReady = false // Reloading alleles should potentially trigger a redraw of the full view

        if (this.selected_interpretation) {
            return this.workflowService
                .loadAlleles(
                    this.type,
                    this.id,
                    this.selected_interpretation,
                    this.selected_interpretation.current // Whether to show current allele data or historical data
                )
                .then((alleles) => {
                    this.selected_interpretation_alleles = alleles
                    if (setViewReady) this.isViewReady = true // Reloading alleles should potentially trigger a redraw of the full view
                    console.log(
                        '(Re)Loaded alleles from interpretation...',
                        this.selected_interpretation_alleles
                    )
                })
        } else if (this.type === 'allele') {
            // Fetch allele directly if no interpretation is set
            return this.alleleService
                .getAlleles(this.id, null, this.genepanel_name, this.genepanel_version)
                .then((a) => {
                    return this.alleleService
                        .updateACMG(a, this.genepanel_name, this.genepanel_version, [])
                        .then(() => {
                            this.alleles = a
                            if (setViewReady) this.isViewReady = true // Reloading alleles should potentially trigger a redraw of the full view
                            console.log('(Re)Loaded alleles directly...', this.alleles)
                        })
                })
        }
    }

    setGenepanelOptions(genepanel_options) {
        this.genepanel_options = genepanel_options
        if (!genepanel_options) {
            this.genepanel_options_selected = null
        }
        if (genepanel_options && !genepanel_options.includes(this.genepanel_options_selected)) {
            this.genepanel_options_selected = genepanel_options[0]
        }
    }

    loadGenepanel() {
        this.isViewReady = false // Reloading genepanel should trigger a redraw of the full view
        let interpretation = this.getSelected()

        let gp_name = interpretation.genepanel_name
        let gp_version = interpretation.genepanel_version

        this.workflowResource.getGenepanel(this.type, this.id, gp_name, gp_version).then((gp) => {
            this.selected_interpretation_genepanel = gp
            this.isViewReady = true
        })
    }

    loadAnalysis(id) {
        this.analysisResource.getAnalysis(id).then((a) => {
            this.analysis = a
        })
    }

    getSelected() {
        // Fall back to dummy interpretation, if selected interpretation is not defined (for alleles only)
        if (this.selected_interpretation) {
            return this.selected_interpretation
        } else if (this.type === 'allele') {
            return this.dummy_interpretation
        }
    }

    getAll() {
        return this.interpretations ? this.interpretations : [this.dummy_interpretation]
    }

    getHistory() {
        return this.history_interpretations
    }

    isOngoing() {
        let interpretation = this.getSelected()
        return interpretation && interpretation.status === 'Ongoing'
    }

    getGenepanel() {
        return this.selected_interpretation_genepanel
    }

    readOnly() {
        let interpretation = this.getSelected()
        if (!interpretation) {
            return true
        }

        return !this.isOngoing() || interpretation.user.id !== this.user.getCurrentUserId()
    }

    getAlleles() {
        // Fall back to this.alleles when no interpretation exists on backend
        return this.selected_interpretation_alleles || this.alleles
    }

    getAnalysis() {
        return this.analysis
    }
}
