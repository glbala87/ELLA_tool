/* jshint esnext: true */

import {Directive, Inject} from '../ng-decorators';

@Directive({
    selector: 'overview',
    templateUrl: 'ngtmpl/overview.ngtmpl.html',
    scope: {
        selectedView: '='
    }
})
@Inject('$scope', '$interval', 'SearchResource', 'AnnotationjobResource', 'AnnotateVCFFileModal')
export class MainController {
    constructor($scope, $interval, SearchResource, AnnotationjobResource, AnnotateVCFFileModal) {
        this.scope = $scope;
        this.interval = $interval;
        this.searchResource = SearchResource;
        this.annotationjobResource = AnnotationjobResource;
        this.annotateVCFFileModal = AnnotateVCFFileModal;



        this.search = {
            results: null,
            query: ''
        }
        this.annotationJobStatus = {running: 0, completed: 0, failed: 0}; // Number of running, completed and failed jobs
        this.pollForAnnotationJobs();

    }

    updateSearch() {
        if (this.search.search_query && this.search.search_query.length > 2) {
            SearchResource.get(this.search.search_query).then(r => {
                this.search.results = r;
            });
        }
        else {
            this.search.results = null;
        }
    }

    hasSearchResults() {
        return this.search.results || false;
    }

    setView(view) {
        this.selectedView = view;
    }

    isActive(view) {
        return this.selectedView === view;
    }

    showAnnotateVCFFile() {
        this.annotateVCFFileModal.show();
    }

    pollForAnnotationJobs() {
        let cancel = this.interval(() => this.getAnnotationjobs(), 5000);
        this.scope.$on('$destroy', () => this.interval.cancel(cancel));
    }


    getAnnotationjobs() {
        this.annotationjobResource.get().then((res) => {
            let annotationJobStatus = {running: 0, completed: 0, failed: 0};

            // this.annotationJobStatus.running = 0;
            // this.annotationJobStatus.completed = 0;
            // this.annotationJobStatus.failed = 0;

            for (let i=0; i<res.length; i++) {
                let job = res[i];
                let status = job.status;
                if (status.contains("FAILED")) {
                    annotationJobStatus.failed += 1
                } else if (status.contains("DONE")) {
                    annotationJobStatus.completed += 1
                } else {
                    annotationJobStatus.running += 1
                }
            }

            this.annotationJobStatus = annotationJobStatus;
        })
    }


}
