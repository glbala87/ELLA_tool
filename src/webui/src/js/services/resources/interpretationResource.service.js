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

    get(id) {
        return new Promise((resolve, reject) => {
            let InterpretationRS = this.resource(`${this.base}/interpretations/:id/`);
            let interpretation = InterpretationRS.get({
                id: id
            }, () => {
                resolve(new Interpretation(interpretation));
            });
        });
    }

    getAlleles(id) {
        return new Promise((resolve, reject) => {
            let AlleleRS = this.resource(`${this.base}/interpretations/:id/alleles/`);
            let alleles = AlleleRS.query({id: id}, () => {
                resolve(alleles);
            });
        });
    }

    updateState(interpretation) {
        return new Promise((resolve, reject) => {
            let InterpretationRS = this.resource(
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
            InterpretationRS.update(data, resolve, reject);
        });
    }



}

export default InterpretationResource;
