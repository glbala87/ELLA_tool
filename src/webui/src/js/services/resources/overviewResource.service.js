/* jshint esnext: true */

import {Service, Inject} from '../../ng-decorators';
import {Allele} from '../../model/allele';
import Analysis from '../../model/analysis';

@Service({
    serviceName: 'OverviewResource'
})
@Inject('$resource')
export class OverviewResource {

    constructor(resource) {
        this.resource = resource;
        this.base = '/api/v1';
    }

    getAllelesOverview() {
        return new Promise((resolve, reject) => {
            let uri = `${this.base}/overviews/alleles/`;
            let r = this.resource(uri);
            let overview = r.get((data) => {

                // Convert to our model objects
                for (let key of ['marked_review', 'marked_medicalreview', 'missing_alleleassessment', 'ongoing']) {
                    for (let item of data[key]) {
                        item.allele = new Allele(item.allele);
                    }
                }

                resolve(overview);
            }, reject);
        });
    }

    getAllelesFinalizedOverview(page) {
        return new Promise((resolve, reject) => {
            page = page ? page : 1;
            let uri = `${this.base}/overviews/alleles/finalized/?page=${page}&per_page=10`;
            let r = this.resource(uri);
            let overview = r.query((data, headers) => {
                headers = headers()
                let pagination = {
                    page: headers['page'],
                    totalCount: headers['total-count'],
                    perPage: headers['per-page'],
                    totalPages: headers['total-pages'],
                }
                resolve({
                    pagination: pagination,
                    data: data.map(a => {
                        a.allele = new Allele(a.allele)
                        return a
                    })
                });
            }, reject);
        });
    }

    getAnalysesOverview(by_findings=false) {
        return new Promise((resolve, reject) => {
            let uri = `${this.base}/overviews/analyses/`;
            if (by_findings) {
                uri += 'by-findings/';
            }
            let r = this.resource(uri);
            let overview = r.get((data) => {

                let categories = [
                    'ongoing',
                ]

                if (by_findings) {
                    categories = categories.concat([
                        'not_started_with_findings',
                        'not_started_without_findings',
                        'not_started_missing_alleleassessments',
                        'marked_review_with_findings',
                        'marked_review_without_findings',
                        'marked_review_missing_alleleassessments',
                    ]);
                }
                else {
                    categories = categories.concat([
                        'not_started',
                        'marked_review',
                        'marked_medicalreview',
                    ]);
                }

                for (let key of categories) {
                    data[key] = data[key].map(a => new Analysis(a));
                }

                resolve(overview);
            }, reject);
        });
    }

    getAnalysesFinalizedOverview(page) {
        return new Promise((resolve, reject) => {
            page = page ? page : 1;
            let uri = `${this.base}/overviews/analyses/finalized/?page=${page}&per_page=10`;
            let r = this.resource(uri);
            let overview = r.query((data, headers) => {
                headers = headers()
                let pagination = {
                    page: headers['page'],
                    totalCount: headers['total-count'],
                    perPage: headers['per-page'],
                    totalPages: headers['total-pages'],
                }
                resolve({
                    pagination: pagination,
                    data: data.map(a => new Analysis(a))
                });
            }, reject);
        });
    }

    getActivities() {
        return new Promise((resolve, reject) => {
            let uri = `${this.base}/overviews/activities/`;
            let r = this.resource(uri);
            let overview = r.query((data) => {

                for (let d of data) {
                    if ('allele' in d) {
                        d['allele'] = new Allele(d['allele'])
                    }
                    if ('analysis' in d) {
                        d['analysis'] = d['analysis']
                    }
                }

                resolve(overview);
            }, reject);
        });
    }

    getUserStats() {
        return new Promise((resolve, reject) => {
            let uri = `${this.base}/overviews/userstats/`;
            let r = this.resource(uri);
            let overview = r.get((data) => {
                resolve(overview);
            }, reject);
        });
    }

}

