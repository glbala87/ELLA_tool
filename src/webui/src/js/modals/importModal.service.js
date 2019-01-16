'use strict'
import toastr from 'toastr'
import { Service, Inject } from '../ng-decorators'
import { UUID } from '../util'
import { ImportData } from '../model/importdata'
import template from './importModal.ngtmpl.html'
import popover from '../widgets/annotationjobPopover.ngtmpl.html'

export class ImportController {
    constructor(modalInstance, User, AnnotationjobResource, $interval, $filter, $scope) {
        this.modal = modalInstance
        this.user = User.getCurrentUser()
        this.annotationjobResource = AnnotationjobResource
        this.filter = $filter
        this.user = User.getCurrentUser()

        this.analyses = []
        this.jobData = null
        this.annotationjobs = null
        this.annotationjobPage = 1

        this.rawInput = ''

        this.interval = $interval
        this.scope = $scope

        // FIXME: ng-change on uib-pagination doesn't correctly enable next-button
        // Watch annotationjobPage, and enable next-button if relevant
        this.scope.$watch(() => this.annotationjobPage, () => this.getAnnotationjobs())

        this.annotationjobResource.annotationServiceRunning().then((isAlive) => {
            if (!isAlive) {
                toastr.error(
                    'Unable to connect to annotation service. Contact support to restart the annotation service.'
                )
            }
        })
        this.pollForAnnotationJobs()
    }

    pollForAnnotationJobs() {
        let cancel = this.interval(() => this.getAnnotationjobs(), 5000)
        this.scope.$on('$destroy', () => this.interval.cancel(cancel))
    }

    getAnnotationjobs() {
        let popups_open = document.getElementsByClassName('annotationjobinfo').length > 0
        if (!popups_open) {
            this.annotationjobPageChanged()
        }
    }

    annotationjobPageChanged() {
        this.annotationjobResource.get(null, 8, this.annotationjobPage).then((res) => {
            this.annotationjobs = res
            this.annotationjobPage = res.pagination.page

            // FIXME: uib-pagination doesn't enable next-button as it should
            if (this.annotationjobPage < res.pagination.totalPages) {
                let next_element = document
                    .getElementsByClassName('annotationjobpagination')[0]
                    .getElementsByClassName('pagination-next')[0]
                next_element.classList.remove('disabled')
            }
        })
    }

    restartJob(id) {
        this.annotationjobResource.restart(id)
    }

    parseInput() {
        let splitInput = {}

        // Find lines starting with '-'
        let lines = this.rawInput.split('\n')
        let currentFile = ''
        let uuid = null
        for (let l of lines) {
            if (l.trim() === '') continue

            // Check if start of new file
            if (!uuid || l.startsWith('-')) {
                uuid = UUID()
                if (l.startsWith('-')) {
                    currentFile = l.replace(/-*\s*/g, '')
                } else {
                    currentFile = ''
                }

                splitInput[uuid] = {
                    filename: currentFile,
                    fileContents: ''
                }

                // Don't include line in contents if it is a separator line
                if (l.startsWith('-')) continue
            }
            splitInput[uuid].fileContents += l + '\n'
        }

        let jobData = {}
        for (let k in splitInput) {
            jobData[k] = new ImportData(splitInput[k].filename, splitInput[k].fileContents)
        }
        this.jobData = jobData
    }

    getImportDescription() {
        let incomplete = 0
        let createAnalyses = 0
        let standaloneVariants = 0
        let appendAnalyses = []
        let appendVariants = 0

        for (let j of Object.values(this.jobData)) {
            if (!j.isSelectionComplete()) {
                incomplete += 1
            } else if (j.isCreateNewAnalysisType()) {
                createAnalyses += 1
            } else if (j.isAppendToAnalysisType()) {
                appendAnalyses.push(j.importSelection.analysis.name)
                appendVariants += Object.values(j.contents.lines).filter((l) => l.include).length
            } else if (j.isVariantMode()) {
                standaloneVariants += Object.values(j.contents.lines).filter((l) => l.include)
                    .length
            }
        }

        appendAnalyses = new Set(appendAnalyses).size

        let description = []
        if (incomplete) {
            let s = `${incomplete} ${incomplete > 1 ? 'imports' : 'import'} incomplete.`
            description.push(s)
        }

        if (createAnalyses) {
            let s = `Create ${createAnalyses} new ${createAnalyses > 1 ? 'analyses' : 'analysis'}.`
            description.push(s)
        }

        if (appendAnalyses) {
            let s = `Append ${appendVariants} ${
                appendVariants > 1 ? 'variants' : 'variant'
            } to ${appendAnalyses} existing ${appendAnalyses > 1 ? 'analyses' : 'analysis'}`
            description.push(s)
        }

        if (standaloneVariants) {
            let s = `Import ${standaloneVariants} standalone ${
                standaloneVariants > 1 ? 'variants' : 'variant'
            }`
            description.push(s)
        }

        return description
    }

    import() {
        let processedJobData = {}
        for (let id in this.jobData) {
            processedJobData[id] = this.jobData[id].process()
        }

        this.modal.close(processedJobData)
    }

    getJobDisplay(job) {
        if (job.sample_id) {
            return `Create new analysis from sample: <i>${job.sample_id} (${job.genepanel_name}_${
                job.genepanel_version
            })</i>`
        } else if (job.mode === 'Analysis' && job.properties.create_or_append === 'Create') {
            return `Create new analysis: <i>${job.properties.analysis_name} (${
                job.genepanel_name
            }_${job.genepanel_version})</i>`
        } else if (job.mode === 'Analysis' && job.properties.create_or_append === 'Append') {
            return `Append to analysis: <i>${job.properties.analysis_name}</i>`
        } else if (job.mode === 'Variants') {
            return `Independent variants: <i>${job.genepanel_name}_${job.genepanel_version}</i>`
        }
    }

    importDisabled() {
        let allReady = Object.values(this.jobData)
            .map((j) => j.isSelectionComplete())
            .every((v) => v)
        return !allReady
    }
}

@Service({
    serviceName: 'ImportModal'
})
@Inject('$uibModal', '$resource', 'User', 'AnnotationjobResource')
export class ImportModal {
    constructor($uibModal, $resource, User, AnnotationjobResource) {
        this.modalService = $uibModal
        this.resource = $resource
        this.base = '/api/v1/'
        this.user = User
        this.annotationjobResource = AnnotationjobResource
    }

    show() {
        let modal = this.modalService.open({
            templateUrl: 'importModal.ngtmpl.html',
            controller: [
                '$uibModalInstance',
                'User',
                'AnnotationjobResource',
                '$interval',
                '$filter',
                '$scope',
                ImportController
            ],
            controllerAs: 'vm',
            backdrop: 'static'
        })

        return modal.result.then((result) => {
            if (result) {
                let promises = []
                for (let k in result) {
                    promises.push(this.annotationjobResource.post(result[k]))
                }
                return Promise.all(promises)
            }
        })
    }
}
