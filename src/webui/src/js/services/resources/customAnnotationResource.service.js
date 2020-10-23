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
}

export default CustomAnnotationResource
