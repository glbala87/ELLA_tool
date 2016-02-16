/* jshint esnext: true */

import {Interpretation} from '../../model/interpretation';
import {Service, Inject} from '../../ng-decorators';


@Service({
    serviceName: 'InterpretationResource'
})
@Inject('$resource')
class InterpretationResource {

    constructor(resource) {
        this.resource = resource;
        this.base = '/api/v1';
    }

    _getInterpretation(id) {
        return new Promise((resolve, reject) => {
            let r = this.resource(`${this.base}/interpretations/:id/`);
            let interpretation = r.get({
                id: id
            }, () => {
                resolve(new Interpretation(interpretation));
            });
        });
    }

    _getAlleles(id) {
        return new Promise((resolve, reject) => {
            let r = this.resource(`${this.base}/interpretations/:id/alleles/`, {}, {
                get: {
                    isArray: true
                }
            });
            let alleles = r.get({
                id: id
            }, () => {
                resolve(alleles);
            });
        });
    }

    get(id) {
        return this._getInterpretation(id);
    }

    getAlleles(id) {
        return this._getAlleles(id);
    }

    updateState(interpretation) {
        return new Promise((resolve, reject) => {
            let r = this.resource(
                `${this.base}/interpretations/:id/`, {
                    id: interpretation.id
                }, {
                    update: {
                        method: 'PATCH'
                    }
                }
            );
            let data = {
                id: interpretation.id,
                state: interpretation.state,
                userState: interpretation.userState,
                status: interpretation.status,
                user_id: interpretation.user_id
            };
            r.update(data, resolve, reject);
        });
    }

    complete(id) {
        return new Promise((resolve, reject) => {
            let r = this.resource(`${this.base}/interpretations/${id}/actions/complete/`, {}, {
                complete: {
                    method: 'PUT'
                }
            });
            r.complete(
                {
                    id: id
                },
                resolve(),
                reject()
            );
        });
    }

    finalize(id) {
        return new Promise((resolve, reject) => {
            let r = this.resource(`${this.base}/interpretations/${id}/actions/finalize/`, {}, {
                finalize: {
                    method: 'PUT'
                }
            });
            r.finalize(
                {
                    id: id
                },
                resolve(),
                reject()
            );
        });
    }

    override(id, user_id) {
        return new Promise((resolve, reject) => {
            let r = this.resource(`${this.base}/interpretations/${id}/actions/override/`, {}, {
                override: {
                    method: 'POST'
                }
            });
            r.override(
                {
                    id: user_id
                },
                resolve,
                reject
            );
        });
    }

    start(id, user_id) {
        return new Promise((resolve, reject) => {
            let r = this.resource(`${this.base}/interpretations/${id}/actions/start/`, {}, {
                start: {
                    method: 'POST'
                }
            });
            r.start(
                {
                    user_id: user_id
                },
                resolve,
                reject
            );
        });
    }

}

export default InterpretationResource;
