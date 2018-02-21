/* jshint esnext: true */

import { Service, Inject } from '../../ng-decorators'

@Service({
    serviceName: 'AnnotationjobResource'
})
@Inject('$resource')
export class AnnotationjobResource {
    constructor(resource) {
        this.resource = resource
        this.base = '/api/v1'
    }

    get(q, per_page, page) {
        return new Promise((resolve, reject) => {
            let args = []
            if (q) {
                args.push(`q=${encodeURIComponent(JSON.stringify(q))}`)
            }
            if (per_page) {
                args.push(`per_page=${per_page}`)
            }
            if (page) {
                args.push(`page=${page}`)
            }

            if (!args.length) {
                var r = this.resource(`${this.base}/import/service/jobs/`)
            } else {
                var r = this.resource(`${this.base}/import/service/jobs/?${args.join('&')}`)
            }

            let annotationjobs = r.query((data, headers) => {
                headers = headers()
                let pagination = {
                    page: headers['page'],
                    totalCount: headers['total-count'],
                    perPage: headers['per-page'],
                    totalPages: headers['total-pages']
                }
                resolve({
                    pagination: pagination,
                    data: data
                })
            }, reject)
        })
    }

    annotationServiceRunning() {
        return new Promise((resolve, reject) => {
            let r = this.resource(
                `${this.base}/import/service/running/`,
                {},
                {
                    get: {
                        method: 'GET'
                        // isArray: false,
                    }
                }
            )
            let isAlive = r.get(() => {
                resolve(isAlive.running)
            })
        })
    }

    post(data) {
        return new Promise(resolve => {
            let r = this.resource(
                `${this.base}/import/service/jobs/`,
                {},
                {
                    post: {
                        method: 'POST'
                    }
                }
            )
            r.post(data, o => {
                resolve(o)
            })
        })
    }

    restart(id) {
        return new Promise((resolve, reject) => {
            let r = this.resource(
                `${this.base}/import/service/jobs/${id}/`,
                {},
                {
                    patch: {
                        method: 'PATCH'
                    }
                }
            )
            let data = { status: 'SUBMITTED' }
            r.patch(
                data,
                res => {
                    resolve(res)
                },
                reject
            )
        })
    }
}
