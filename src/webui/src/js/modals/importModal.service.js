'use strict';
import {Service, Inject} from '../ng-decorators';
import {UUID} from '../util';

export class ImportController {
    constructor(modalInstance, User, AnalysisResource, AnnotationjobResource, toastr, $interval, $filter,$scope) {
        this.modal = modalInstance;
        this.user = User.getCurrentUser();
        this.analysisResource = AnalysisResource;
        this.annotationjobResource = AnnotationjobResource;
        this.toastr = toastr;
        this.filter = $filter;
        this.user = User.getCurrentUser()

        this.analyses = [];
        this.jobData = null;
        this.annotationjobs = null;
        this.annotationjobPage = 1;

        this.rawInput = '';
        this.parsedInput = null;

        this.interval = $interval;
        this.scope = $scope

        // FIXME: ng-change on uib-pagination doesn't correctly enable next-button
        // Watch annotationjobPage, and enable next-button if relevant
        this.scope.$watch(
            () => this.annotationjobPage,
            () => this.getAnnotationjobs()
        )

        this.annotationjobResource.annotationServiceRunning().then((isAlive) => {
            if (!isAlive) {
                this.toastr.error("Unable to connect to annotation service. Start the annotation service and try again", 10000);
            }
        });
        this.pollForAnnotationJobs();

    }

    pollForAnnotationJobs() {
        let cancel = this.interval(() => this.getAnnotationjobs(), 5000);
        this.scope.$on('$destroy', () => this.interval.cancel(cancel));
    }

    getAnnotationjobs() {
        let popups_open = document.getElementsByClassName("annotationjobinfo").length > 0;
        if (!popups_open) {
            this.annotationjobPageChanged()
        }
    }

    annotationjobPageChanged() {
        this.annotationjobResource.get(null, 8, this.annotationjobPage).then((res) => {
            this.annotationjobs = res;
            this.annotationjobPage = res.pagination.page;

            // FIXME: uib-pagination doesn't enable next-button as it should
            if (this.annotationjobPage < res.pagination.totalPages) {
                let next_element = document.getElementsByClassName('annotationjobpagination')[0].getElementsByClassName('pagination-next')[0];
                next_element.classList.remove("disabled")
            }
        })
    }

    restartJob(id) {
        this.annotationjobResource.restart(id);
    }

    parseInput() {
        let parsedInput = {}
        let jobData = {}

        // Find lines starting with '-'
        let lines = this.rawInput.split("\n");
        let currentFile = "";
        let uuid = null;
        for (let l of lines) {
            if (l.trim() == "") continue;

            // Check if start of new file
            if (!uuid || l.startsWith('-')) {
                uuid = UUID()
                if (l.startsWith('-')) {
                    currentFile = l.replace(/-*\s*/g, '')
                } else {
                    currentFile = '';
                }

                parsedInput[uuid] = {
                    filename: currentFile,
                    fileContents: '',
                }

                // Job data will be populated in importsingle
                jobData[uuid] = {
                    mode: null,
                    type: null,
                    genepanel: null,
                    analysis: null,
                    analysisName: "",
                    technology: null,
                    selectionComplete: false,
                    user_id: this.user.id,
                };

                // Don't include line in contents if it is a separator line
                if (l.startsWith('-')) continue;

            }

            parsedInput[uuid].fileContents += l+"\n";
        }

        this.parsedInput = parsedInput;
        this.jobData = jobData;
    }

    getImportDescription() {
        let incomplete = 0;
        let createAnalyses = 0;
        let standaloneVariants = 0;
        let appendAnalyses = [];
        let appendVariants = 0;

        for (let j of Object.values(this.jobData)) {
            if (!j.selectionComplete) {
                incomplete += 1;
            } else if (j.type === "Analysis") {
                if (j.mode === "Create") {
                    createAnalyses += 1;
                } else if (j.mode === "Append") {
                    appendAnalyses.push(j.analysis.name);
                    appendVariants += Object.values(j.contentLines).filter(l => l.include).length;
                }
            } else if (j.type === "Variants") {
                standaloneVariants += Object.values(j.contentLines).filter(l => l.include).length;
            }
        }

        appendAnalyses = new Set(appendAnalyses).size;

        let description = [];
        if (incomplete) {
            let s = `${incomplete} ${incomplete > 1 ? "imports" : "import"} incomplete.`;
            description.push(s);
        }

        if (createAnalyses) {
            let s = `Create ${createAnalyses} new ${createAnalyses > 1 ? "analyses" : "analysis"}.`;
            description.push(s);
        }

        if (appendAnalyses) {
            let s = `Append ${appendVariants} ${appendVariants > 1 ? "variants": "variant"} to ${appendAnalyses} existing ${appendAnalyses > 1 ? "analyses" : "analysis"}`;
            description.push(s);
        }

        if (standaloneVariants) {
            let s = `Import ${standaloneVariants} standalone ${standaloneVariants > 1 ? "variants" : "variant"}`;
            description.push(s);
        }

        return description;
    }

    rebuildFile(header, contentLines) {
        let data = header;
        for (let ld of Object.values(contentLines)) {
            if (ld.include) {
                data += "\n"+ld.contents;
            }
        }
        return data
    }

    import() {
        let processedJobData = {}
        for (let id in this.jobData) {
            let jobdata = this.jobData[id];
            let rebuilt = this.rebuildFile(jobdata.header, jobdata.contentLines)

            let properties = {
                sample_type: jobdata.technology,
            }

            if (jobdata.type === "Analysis") {
                properties.create_or_append = jobdata.mode;
                properties.analysis_name = jobdata.mode === "Append" ? jobdata.analysis.name : jobdata.analysisName;
            }

            processedJobData[id] = {
                data: rebuilt,
                mode: jobdata.type,
                genepanel_name: jobdata.genepanel.name,
                genepanel_version: jobdata.genepanel.version,
                properties: properties,
                user_id: this.user.id,
            }

        }


        this.modal.close(processedJobData)

    }

    importDisabled() {
        let allReady = Object.values(this.jobData).map(j => j.selectionComplete).every(v => v);
        return !allReady;
    }
}

@Service({
    serviceName: 'ImportModal'
})

@Inject('$uibModal', '$resource', 'User', "AnnotationjobResource")
export class ImportModal {

    constructor($uibModal, $resource, User, AnnotationjobResource) {
        this.modalService = $uibModal;
        this.resource = $resource;
        this.base = '/api/v1/';
        this.user = User;
        this.annotationjobResource = AnnotationjobResource;
    }

    show() {
        let modal = this.modalService.open({
            templateUrl: 'ngtmpl/importModal.ngtmpl.html',
            controller: [
                '$uibModalInstance',
                'User',
                "AnalysisResource",
                "AnnotationjobResource",
                "toastr",
                "$interval",
                "$filter",
                "$scope",
                ImportController
            ],
            controllerAs: 'vm',
            size: 'lg',
            backdrop: 'static',
        });

        return modal.result.then((result) => {
            if (result) {
                let promises = []
                for (let k in result) {
                    promises.push(this.annotationjobResource.post(result[k]))
                }
                return Promise.all(promises)
            }
        });
    }
}
