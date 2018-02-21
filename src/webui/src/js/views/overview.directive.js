/* jshint esnext: true */

import { Directive, Inject } from '../ng-decorators'

import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'

app.component('overview', {
    templateUrl: 'ngtmpl/overview-new.ngtmpl.html',
    controller: connect(
        {
            changeSection: signal`views.overview.changeSection`,
            sectionKeys: state`views.overview.sectionKeys`,
            sections: state`views.overview.sections`,
            loading: state`views.overview.loading`
        },
        'Overview'
    )
})

@Directive({
    selector: 'overview-old',
    templateUrl: 'ngtmpl/overview.ngtmpl.html'
})
@Inject(
    '$scope',
    '$interval',
    'Config',
    'Navbar',
    'SearchResource',
    'AnnotationjobResource',
    'ImportModal'
)
export class MainController {
    constructor(
        $scope,
        $interval,
        Config,
        Navbar,
        SearchResource,
        AnnotationjobResource,
        ImportModal
    ) {
        this.scope = $scope
        this.interval = $interval
        this.config = Config.getConfig()
        this.searchResource = SearchResource
        this.annotationjobResource = AnnotationjobResource
        this.importModal = ImportModal

        Navbar.clearItems()

        this.search = {
            results: null,
            query: ''
        }

        this.views = ['analyses', 'analyses-by-findings', 'variants']

        this.view_names = {
            variants: 'Variants',
            analyses: 'Analyses',
            'analyses-by-findings': 'Analyses'
        }

        this.annotationjobStatus = { running: 0, failed: 0 } // Number of running, completed and failed jobs
        this.pollForAnnotationJobs()
    }

    updateSearch() {
        if (this.search.search_query && this.search.search_query.length > 2) {
            SearchResource.get(this.search.search_query).then(r => {
                this.search.results = r
            })
        } else {
            this.search.results = null
        }
    }

    shouldShowView(view) {
        // TODO: Change this to use user config when implemented.
        return this.config.user.user_config.overview.views.includes(view)
    }

    hasMultipleViews() {
        return this.views.filter(x => this.shouldShowView(x)).length > 1
    }

    hasSearchResults() {
        return this.search.results || false
    }

    setView(view) {
        sessionStorage.setItem('overview', view)
    }

    getSelectedView() {
        return sessionStorage.getItem('overview') || this.config.user.user_config.overview.views[0]
    }

    isActive(view) {
        return this.getSelectedView() === view
    }

    showImportModal() {
        this.importModal.show()
    }

    pollForAnnotationJobs() {
        let cancel = this.interval(() => this.getAnnotationJobStatus(), 10000)
        this.scope.$on('$destroy', () => this.interval.cancel(cancel))
        this.getAnnotationJobStatus()
    }

    getAnnotationJobStatus() {
        this.annotationjobResource.get({ status: ['RUNNING', 'SUBMITTED'] }, 1, 1).then(res => {
            this.annotationjobStatus.running = res.pagination.totalCount
        })

        this.annotationjobResource.get({ status: { $like: 'FAILED%' } }, 1, 1).then(res => {
            this.annotationjobStatus.failed = res.pagination.totalCount
        })
    }
}
