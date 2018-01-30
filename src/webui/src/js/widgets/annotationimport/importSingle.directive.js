/* jshint esnext: true */

import {Directive, Inject} from '../../ng-decorators';
import {printedFileSize} from '../../util'

@Directive({
    selector: "importsingle",
    templateUrl: "ngtmpl/importSingle.ngtmpl.html",
    scope: {
        importData: '=',
        index: '=',
    },
})
@Inject('$scope', 'AnalysisResource', '$filter', 'User')
export class ImportSingleController {
    constructor($scope, AnalysisResource, $filter, User) {


        this.scope = $scope;
        this.analysisResource = AnalysisResource;
        this.filter = $filter;
        this.user = User.getCurrentUser()
        this.genepanels = this.user.group.genepanels;


        this.editMode = false;

        this.scope.$watch(
            () => this.importData.importSelection.analysisName,
            () => {
                this.findExistingAnalysis()
            }
        )

        this.scope.$watch(
            () => this.importData.importSelection.analysis,
            () => this.checkAnalysisStatus()
        )

        this.warnings = {
            noGenotype: {
                text: "No genotype found for some or all variants. Can only import as independent variants.",
                active: !this.importData.genotypeAvailable(),
                show: () => {return true},
            },
            multipleAnalyses: {
                text: "Multiple analyses matching filename",
                active: false,
                show: () => {return this.importData.isAnalysisMode()}
            },
            analysisNameMatch: {
                text: "The analysis name matches one or more existing analysis names. Do you really want to create a new analysis? If not, please choose \"Append\" instead.`",
                active: false,
                show: () => {return this.importData.isCreateNewAnalysisType()}
            },
            analysisStarted: {
                text: null,
                active: false,
                show: () => {return this.importData.isAppendToAnalysisType()}
            }
        }

        this.setDefaultChoices()
        if (!this.importData.isSelectionComplete()) {
            this.editMode = true;
        }

    }

    toggleEditMode() {
        this.editMode = !this.editMode;
    }

    setDefaultChoices() {
        // If some or all variants miss genotype, we can not import this to an analysis.
        // Set default mode to variants.
        if (this.warnings.noGenotype.active) {
            this.importData.importSelection.mode = "Variants";
        } else {
            this.importData.importSelection.mode = "Analysis";
        }

        this.importData.importSelection.technology = "Sanger";
        this.importData.importSelection.genepanel = this.user.group.default_import_genepanel ? this.user.group.default_import_genepanel : null;

        let fileNameBase = this.importData.getFileNameBase()

        // Search for matching analysis
        if (fileNameBase.length > 3) {
            var p = this.analysisResource.get({name: {'$ilike': `%${fileNameBase}%`}}, 2)
        } else {
            var p = new Promise((resolve) => {resolve([])})
        }

        this.importData.importSelection.analysisName = fileNameBase;
        p.then((matchingAnalyses) => {
            if (matchingAnalyses.length == 1) {
                this.importData.importSelection.type = "Append";
                this.importData.importSelection.analysis = matchingAnalyses[0]
            } else {
                this.warnings.multipleAnalyses.active = matchingAnalyses.length > 1;
                this.importData.importSelection.type = "Create";
            }
        })
    }

    getSummary() {
        let summary = {};
        if (this.importData.isVariantMode()) {
            summary["mode"] = "Independent variants"
            summary["genepanel"] = this.importData.importSelection.genepanel ? `${this.importData.importSelection.genepanel.name} ${this.importData.importSelection.genepanel.version}` : "";
        } else if (this.importData.isCreateNewAnalysisType()) {
            summary["mode"] = "Create new analysis"
            summary["analysis name"] = this.importData.importSelection.analysisName;
            summary["genepanel"] = this.importData.importSelection.genepanel ? `${this.importData.importSelection.genepanel.name} ${this.importData.importSelection.genepanel.version}` : "";
        } else if (this.importData.isAppendToAnalysisType()) {
            summary["mode"] = "Append to analysis"
            summary["analysis"] = this.importData.importSelection.analysis ? this.importData.importSelection.analysis.name : "";
        }

        summary["technology"] = this.importData.importSelection.technology;

        return summary;
    }

    updateAnalysisOptions(text) {
        return this.analysisResource.get({name: {$ilike: `%${text}%`}}, 20).then( (analyses) => {
            this.analyses = analyses;
            return this.analyses;
            }
        )
    }

    showWarning(warning) {
        return warning.active && warning.show()
    }

    /*
     * Check if selected analysis is started
     */
    _analysisInReview(statuses) {
        return statuses.length > 1 && statuses[statuses.length-1] === "Not started" && statuses[statuses.length-2] === "Done";
    }

    _analysisOngoing(statuses) {
        return statuses[statuses.length-1] === "Ongoing";
    }

    _analysisDone(statuses) {
        return statuses[statuses.length-1] === "Done";
    }

    analysisIsStarted() {
        if (!this.importData.importSelection.analysis) return false;
        else {
            let statuses = this.importData.importSelection.analysis.interpretations.map(i => i.status)
            return this._analysisDone(statuses) || this._analysisOngoing(statuses) || this._analysisInReview(statuses);
        }
    }

    checkAnalysisStatus() {
        if (!this.analysisIsStarted()) {
            this.warnings.analysisStarted.active = false;
            this.warnings.analysisStarted.text = null;
            return;
        }
        let last_interpretation = this.importData.importSelection.analysis.interpretations[this.importData.importSelection.analysis.interpretations.length-1]
        let statuses = this.importData.importSelection.analysis.interpretations.map(i => i.status)
        let s = "Analysis is ";
        if (this._analysisDone(statuses)) {
            s += "finalized. Appending to this analyses will reopen it."
        } else if (this._analysisOngoing(statuses)) {
            s += "ongoing."
        } else if (this._analysisInReview(statuses)) {
            s += "in review."
        }

        s += " ("
        if (last_interpretation.user) {
            s += `${last_interpretation.user.abbrev_name}, `
        }
        let interpretation_date = this.filter('date')(last_interpretation.date_last_update, 'dd-MM-yyyy HH:mm');
        s += `${interpretation_date})`

        this.warnings.analysisStarted.active = true;
        this.warnings.analysisStarted.text = s;
    }


    /*
     * Check if there exists an analysis with a similar name
     */
    findExistingAnalysis() {
        // Don't match if typed in analysis name is less than 5
        if (this.importData.importSelection.analysisName.length < 5) {
            this.warnings.analysisNameMatch.active = false;
            return;
        }
        let p_name = this.analysisResource.get({name: {$ilike: `%${this.importData.importSelection.analysisName}%`}}, 2)

        // Extract longest substring of digits
        let subnumber = "";
        let re = /\d+/g;
        let m = null;
        do {
            m = re.exec(this.importData.importSelection.analysisName)
            if (m && m[0].length > subnumber.length) {
                subnumber = m[0];
            }
        } while (m);

        // Don't match on subnumber if length < 5
        subnumber = ""+subnumber;
        if (subnumber.length < 5) {
            var p_number = new Promise((resolve) => {resolve([])})
        } else {
            var p_number = this.analysisResource.get({name: {$like: `%${subnumber}%`}}, 2)
        }

        // Try to match against existing analyses, based on either full string or subnumber
        Promise.all([p_name, p_number]).then( (matchingAnalyses) => {
            matchingAnalyses = [].concat.apply([], matchingAnalyses)
            let matchingAnalysesNames = new Array(...new Set(matchingAnalyses.map(a => a.name)))
            this.warnings.analysisNameMatch.active = matchingAnalysesNames.length > 0;
        })
    }
}
