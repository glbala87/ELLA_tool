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
            let r = this.resource(`${this.base}/annotationjobs/`);
            let annotationjobs = r.query(() => {
                resolve(annotationjobs);
            }, reject);
        });
    }

    annotationServiceRunning() {
        return new Promise((resolve, reject) => {
            let r = this.resource(`${this.base}/annotationservice/running/`, {},
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
            let r = this.resource(`${this.base}/annotationjobs/`, {},
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
            let r = this.resource(`${this.base}/annotationjobs/`, {},
                {
                    patch: {
                        method: 'PATCH'
                    }
                });
            let data = {id: id, status: "SUBMITTED"};
            r.patch(data, res => {
                resolve(res);
            }, reject);
        });
    }

    delete(id) {
        return new Promise((resolve, reject)=> {
            console.log(`${this.base}/annotationjobs/${id}`);
            let r = this.resource(`${this.base}/annotationjobs/${id}`, {},
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
