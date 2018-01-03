/* jshint esnext: true */

import {Directive, Inject} from '../../ng-decorators';
import {printedFileSize} from '../../util'

@Directive({
    selector: "importsingle",
    templateUrl: "ngtmpl/importSingle.ngtmpl.html",
    scope: {
        fileContents: "=",
        filename: "=",
        genepanels: "=",
        jobData: '=',
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

        this.jobData.fileType = "Unknown";

        this.types = ["Analysis", "Variants"];
        this.jobData.type = this.types[0];
        this.modes = ["Create", "Append"];

        this.jobData.mode = this.modes[0];
        this.technologies = ["Sanger", "HTS"];
        this.jobData.technology = this.technologies[0];

        this.jobData.analysis = null;
        this.jobData.analysisName = "";
        this.jobData.genepanel = null;

        this.editMode = false;

        this.scope.$watch(
            () => this.jobData.analysisName,
            () => {
                this.findExistingAnalysis()
            }
        )

        this.scope.$watch(
            () => this.jobData.analysis,
            () => this.checkAnalysisStatus()
        )

        this.scope.$watch(
            () => this.isSelectionComplete(),
            () => {
                this.jobData.selectionComplete = this.isSelectionComplete();
                if (!this.jobData.selectionComplete) {
                    this.editMode = true;
                }
            }
        )

        this.warnings = {
            noGenotype: {
                text: "No genotype found for some or all variants. Can only import as independent variants.",
                active: false,
            },
            multipleAnalyses: {
                text: "Multiple analyses matching filename",
                active: false,
            },
            analysisNameMatch: {
                text: "The analysis name matches one or more existing analysis names. Do you really want to create a new analysis? If not, please choose \"Append\" instead.`",
                active: false,
                modes: ["Create"]
            },
            analysisStarted: {
                text: null,
                active: false,
                modes: ["Append"]
            }
        }

        this.parseFile()
        this.setDefaultChoices()

    }

    toggleEditMode() {
        this.editMode = !this.editMode;
    }

    parseFile() {
        let lines = this.fileContents.trim().split('\n');
        let header = ""
        let contentLines = {};
        for (let l of lines) {
            if (l.trim() === "") {
                continue;
            }
            if (l.trim().startsWith("#CHROM")) {
                this.jobData.fileType = "vcf"
            } else if (l.trim().startsWith("Index")) {
                this.jobData.fileType = "seqpilot";
            }

            if (l.trim().startsWith("#") || l.trim().startsWith("Index")) {
                header += l +"\n"
                continue;
            }
            let key;
            if (this.jobData.fileType === "vcf") {
                key = this.parseVcfLine(l)
            } else if (this.jobData.fileType === "seqpilot") {
                key = this.parseSeqPilotLine(l)
            } else {
                key = this.parseGenomicOrHGVScLine(l);
            }

            contentLines[key] = {
                contents: l,
                include: true,
            }
        }

        this.jobData.contentLines = contentLines;
        this.jobData.header = header.trim();
    }

    parseVcfLine(line) {
        let vals = line.trim().split("\t")
        let chrom = vals[0];
        let pos = vals[1];
        let ref = vals[3];
        let alt = vals[4];

        let format = vals[8];
        let sample = vals[9];

        let genotype;
        let gt_index = format.split(':').indexOf("GT");
        if (gt_index < 0) {
            genotype = "?/?"
            this.warnings.noGenotype.active = true;
        } else {
            genotype = sample.split(':')[gt_index];
        }

        return `${chrom}:${pos} ${ref}>${alt} (${genotype})`

    }

    parseSeqPilotLine(line) {
        let vals = line.trim().split("\t");
        let transcript = vals[2];
        let cdna = vals[11];
        let genotype = vals[6].match(/\(het\)|\(hom\)/);
        if (!genotype) {
            this.warnings.noGenotype.active = true;
            genotype = "(?)"
        }

        return `${transcript}.${cdna} ${genotype}`
    }

    parseGenomicOrHGVScLine(line) {
        let genotype = line.match(/[\(-]+(het|hom)\)?/)
        if (!genotype) {
            this.warnings.noGenotype.active = true;
        }
        return line
    }


    setDefaultChoices() {
        // If some or all variants miss genotype, we can not import this to an analysis.
        // Set default type to variants.
        if (this.warnings.noGenotype.active) {
            this.jobData.type = "Variants";
        } else {
            this.jobData.type = "Analysis";
        }

        this.technology = "Sanger";
        this.jobData.genepanel = this.user.group.default_import_genepanel ? this.user.group.default_import_genepanel : null;

        let fileNameBase = this.filename ? this.filename.split(".").slice(0,-1).join('.') : '';
        // Search for matching analysis
        if (fileNameBase.length > 3) {
            var p = this.analysisResource.get({name: {'$ilike': fileNameBase}}, 2)
        } else {
            var p = new Promise((resolve) => {resolve([])})
        }

        this.jobData.analysisName = fileNameBase;
        p.then((matchingAnalyses) => {
            if (matchingAnalyses.length == 1) {
                this.jobData.mode = "Append";
                this.jobData.analysis = matchingAnalyses[0]
            } else {
                this.warnings.multipleAnalyses.active = matchingAnalyses.length > 1;
                this.jobData.mode = "Create";
            }
        })
    }

    getSummary() {
        let summary = {
            type: this.jobData.type,
        }

        if (this.jobData.type === "Variants") {
            summary["type"] = "Independent variants"
            summary["genepanel"] = this.jobData.genepanel ? `${this.jobData.genepanel.name} ${this.jobData.genepanel.version}` : "";
        } else if (this.jobData.mode === "Create") {
            summary["type"] = "Create new analysis"
            summary["analysis name"] = this.jobData.analysisName;
            summary["genepanel"] = this.jobData.genepanel ? `${this.jobData.genepanel.name} ${this.jobData.genepanel.version}` : "";
        } else if (this.jobData.mode === "Append") {
            summary["type"] = "Append to analysis"
            summary["analysis"] = this.jobData.analysis ? this.jobData.analysis.name : "";
        }

        summary["technology"] = this.technology;

        return summary;
    }

    isSelectionComplete() {
        let a = this.jobData.type === "Variants" && this.jobData.genepanel;
        let b = this.jobData.type === "Analysis" && this.jobData.mode === "Create" && this.jobData.analysisName && this.jobData.genepanel;
        let c = this.jobData.type === "Analysis" && this.jobData.mode === "Append" && this.jobData.analysis;
        let d = Object.values(this.jobData.contentLines).filter(c => c.include).length

        return Boolean((a || b || c) && d);
    }


    updateAnalysisOptions(text) {
        return this.analysisResource.get({name: {$ilike: text}}, 20).then( (analyses) => {
            this.analyses = analyses;
            return this.analyses;
            }
        )
    }

    showWarning(warning) {

        if (!warning.active) return false;
        else if (warning.modes === undefined) return true;
        else if (warning.modes.indexOf(this.jobData.mode) > -1) return true;
        else return false;
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
        if (!this.jobData.analysis) return false;
        else {
            let statuses = this.jobData.analysis.interpretations.map(i => i.status)
            return this._analysisDone(statuses) || this._analysisOngoing(statuses) || this._analysisInReview(statuses);
        }
    }

    checkAnalysisStatus() {
        if (!this.analysisIsStarted()) {
            this.warnings.analysisStarted.active = false;
            this.warnings.analysisStarted.text = null;
            return;
        }
        let last_interpretation = this.jobData.analysis.interpretations[this.jobData.analysis.interpretations.length-1]
        let statuses = this.jobData.analysis.interpretations.map(i => i.status)
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
        if (this.jobData.analysisName.length < 5) {
            this.warnings.analysisNameMatch.active = false;
            return;
        }
        let p_name = this.analysisResource.get({name: {$ilike: this.jobData.analysisName}}, 2)

        // Extract longest substring of digits
        let subnumber = "";
        let re = /\d+/g;
        let m = null;
        do {
            m = re.exec(this.jobData.analysisName)
            if (m && m[0].length > subnumber.length) {
                subnumber = m[0];
            }
        } while (m);

        // Don't match on subnumber if length < 5
        subnumber = ""+subnumber;
        if (subnumber.length < 5) {
            var p_number = new Promise((resolve) => {resolve([])})
        } else {
            var p_number = this.analysisResource.get({name: {$like: subnumber}}, 2)
        }


        // Try to match against existing analyses, based on either full string or subnumber
        Promise.all([p_name, p_number]).then( (matchingAnalyses) => {
            matchingAnalyses = [].concat.apply([], matchingAnalyses)
            let matchingAnalysesNames = new Array(...new Set(matchingAnalyses.map(a => a.name)))
            this.warnings.analysisNameMatch.active = matchingAnalysesNames.length > 0;
        })
    }




}
