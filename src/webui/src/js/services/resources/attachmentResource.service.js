import { Service, Inject } from '../../ng-decorators'

@Service({
    serviceName: 'AttachmentResource'
})
@Inject('$resource')
class AttachmentResource {
    constructor(resource) {
        this.base = '/api/v1'
        this.resource = resource
    }

    post(file) {
        return new Promise((resolve) => {
            let fd = new FormData()
            fd.append('file', file)
            let r = this.resource(
                `${this.base}/attachments/upload/`,
                {},
                {
                    post: {
                        method: 'POST',
                        transformRequest: angular.identity,
                        // Let's the browser determine the correct content type (https://snippetrepo.com/snippets/file-upload-in-angularjs)
                        headers: { 'Content-Type': undefined },
                        isArray: false
                    }
                }
            )
            r.post(fd, (o) => {
                resolve(o.id)
            })
        })
    }
}

export default AttachmentResource
