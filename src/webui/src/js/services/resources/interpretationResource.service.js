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

    get(id) {
        return this._getInterpretation(id);
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
                user_state: interpretation.user_state,
                status: interpretation.status,
                user_id: interpretation.user_id
            };
            r.update(data, resolve, reject);
        });
    }



}

export default InterpretationResource;
