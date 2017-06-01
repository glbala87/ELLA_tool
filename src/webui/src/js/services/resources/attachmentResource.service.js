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
            let r = this.resource(`${this.base}/attachments/upload/`, {},
                {
                    post: {
                        method: 'POST',
                        transformRequest: angular.identity,
                        headers: {'Content-Type': undefined},
                        isArray: false,
                    }
                });
            r.post(fd, o => {
                resolve(o.id)
            });
        })
    }

    getByIds(ids) {
        return new Promise((resolve, reject) => {
            if (!ids.length) {
                resolve([]);
            }
            let q = JSON.stringify({'id': ids});
            let r = this.resource(`${this.base}/attachments/?q=${encodeURIComponent(q)}`);
            let attachments = r.query(() => {
                let attchmts = [];
                for (let o of attachments) {
                    attchmts.push(o);
                }
                resolve(attchmts);
            });
        });
    }

}


export default AttachmentResource;
