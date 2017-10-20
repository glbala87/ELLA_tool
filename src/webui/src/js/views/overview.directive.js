/* jshint esnext: true */

import {Directive, Inject} from '../ng-decorators';

@Directive({
    selector: 'overview',
    templateUrl: 'ngtmpl/overview.ngtmpl.html',
})
@Inject('$scope', '$interval', 'Config', 'SearchResource', 'AnnotationjobResource', 'AnnotateVCFFileModal')
export class MainController {
    constructor($scope, $interval, Config, SearchResource, AnnotationjobResource, AnnotateVCFFileModal) {
        this.scope = $scope;
        this.interval = $interval;
        this.config = Config.getConfig();
        this.searchResource = SearchResource;
        this.annotationjobResource = AnnotationjobResource;
        this.annotateVCFFileModal = AnnotateVCFFileModal;

        this.search = {
            results: null,
            query: ''
        }

        this.views = [
            'analyses',
            'analyses-by-findings',
            'variants'
        ]

        this.view_names = {
            variants: 'Variants',
            analyses: 'Analyses',
            'analyses-by-findings': 'Analyses'
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

    shouldShowView(view) {
        // TODO: Change this to use user config when implemented.
        return this.config.user.user_config.overview.views.includes(view);
    }

    hasMultipleViews() {
        return this.views.filter((x) => this.shouldShowView(x)).length > 1
    }

    hasSearchResults() {
        return this.search.results || false;
    }

    setView(view) {
        sessionStorage.setItem("overview", view)
    }

    getSelectedView() {
        return sessionStorage.getItem("overview") || this.config.user.user_config.overview.views[0];
    }

    isActive(view) {
        return this.getSelectedView() === view;
    }

    showAnnotateVCFFile() {
        this.annotateVCFFileModal.show();
    }

    pollForAnnotationJobs() {
        let cancel = this.interval(() => this.getAnnotationjobs(), 10000);
        this.scope.$on('$destroy', () => this.interval.cancel(cancel));
        this.getAnnotationjobs();
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
