/* jshint esnext: true */

import { Service, Inject } from '../../ng-decorators'

@Service({
    serviceName: 'CustomAnnotationResource'
})
@Inject('$resource', 'User')
class CustomAnnotationResource {
    constructor(resource, User) {
        this.resource = resource
        this.base = '/api/v1'
        this.user = User
    }

    getByAlleleIds(allele_ids) {
        return new Promise((resolve, reject) => {
            let q = JSON.stringify({
                date_superceeded: null,
                allele_id: allele_ids
            })
            let r = this.resource(`${this.base}/customannotations/?q=${encodeURIComponent(q)}`)
            let customannotations = r.query(() => {
                resolve(customannotations)
            }, reject)
        })
    }

    createOrUpdateCustomAnnotation(allele_id, annotation_data) {
        let data = {
            allele_id,
            annotations: annotation_data,
            user_id: this.user.getCurrentUserId()
        }
        return new Promise(resolve => {
            let r = this.resource(
                `${this.base}/customannotations/`,
                {},
                { createOrUpdate: { method: 'POST' } }
            )
            r.createOrUpdate(data, o => {
                resolve(o)
            })
        })
    }
}

export default CustomAnnotationResource
