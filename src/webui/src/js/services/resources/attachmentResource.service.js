import {Service, Inject} from '../../ng-decorators';

@Service({
    serviceName: 'AttachmentResource'
})
@Inject('$resource')
class AttachmentResource {

    constructor(resource) {
        this.base = '/api/v1';
        this.resource = resource;
    }

    post(file) {
        return new Promise(resolve => {
            let fd = new FormData()
            fd.append("file", file)
            let r = this.resource(`${this.base}/attachments/`, {},
                {
                    post: {
                        method: 'POST',
                        transformRequest: angular.identity,
                        headers: {'Content-Type': undefined}
                    }
                });
            r.post(fd, o => {
                resolve(o)
            });
        })
    }

    getAttachment(id) {
        return new Promise((resolve, reject) => {
            let r = this.resource(`${this.base}/attachments/${id}`, {}, {
                get: {
                    isArray: false
                }
            });
            let attachment = r.get(function () {
                console.log(attachment)
                resolve(attachment);
            });
        });
    }
}


export default AttachmentResource;
