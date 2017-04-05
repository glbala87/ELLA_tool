/* jshint esnext: true */

import {Service, Inject} from '../../ng-decorators';

@Service({
    serviceName: 'LoginResource'
})
@Inject('$resource')
class LoginResource {

    constructor(resource) {
        this.resource = resource;
    }

    login(username, password) {
        return new Promise((resolve, reject) => {
            let credentials = {
                "username": username,
                "password": password
            }
            var r = this.resource(`/api/v1/users/actions/login`, {}, {
                login: {
                    method: "POST",
                }
            });

            var result = r.login(credentials, () => {
                resolve(result)
            }, reject)
        });
    }
}

export default LoginResource;
