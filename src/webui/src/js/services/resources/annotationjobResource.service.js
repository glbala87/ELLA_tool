/* jshint esnext: true */

import {Service, Inject} from '../../ng-decorators';

@Service({
    serviceName: 'AnnotationjobResource'
})
@Inject('$resource')
export class AnnotationjobResource {

    constructor(resource) {
        this.resource = resource;
        this.base = '/api/v1';
    }

    get() {
        return new Promise((resolve, reject) => {
            let r = this.resource(`${this.base}/import/jobs/`);
            let annotationjobs = r.query(() => {
                resolve(annotationjobs);
            }, reject);
        });
    }

    annotationServiceRunning() {
        return new Promise((resolve, reject) => {
            let r = this.resource(`${this.base}/import/service/running/`, {},
                {
                    get: {
                        method: 'GET',
                        // isArray: false,
                    }
            });
            let isAlive = r.get(() => {
                resolve(isAlive.running);
            });
        });
    }

    post(data) {
        return new Promise(resolve => {
            let r = this.resource(`${this.base}/import/jobs/`, {},
                {
                    post: {
                        method: 'POST'
                    }
                });
            r.post(data, o => {
                resolve(o)
            });
        })
    }

    restart(id) {
        return new Promise((resolve, reject)=> {
            let r = this.resource(`${this.base}/import/jobs/${id}/`, {},
                {
                    patch: {
                        method: 'PATCH'
                    }
                });
            let data = {status: "SUBMITTED"};
            r.patch(data, res => {
                resolve(res);
            }, reject);
        });
    }

    delete(id) {
        return new Promise((resolve, reject)=> {
            let r = this.resource(`${this.base}/import/jobs/${id}/`, {},
                {
                    delete: {
                        method: 'DELETE'
                    }
                });
            let del_query = r.delete(() => {
                resolve(del_query);
            }, reject);
        })
    }
}
