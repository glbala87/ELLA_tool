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
            var r = this.resource(`/api/v1/users/actions/login/`, {}, {
                login: {
                    method: "POST",
                }
            });

            var result = r.login(credentials, () => {
                resolve(result)
            }, (error) => {
                console.log(error)
                console.log(error.data)
                reject(error.data)
            })
        });
    }

    logout() {
        return new Promise((resolve, reject) => {
            var r = this.resource(`/api/v1/users/actions/logout/`, {}, {
                login: {
                    method: "POST",
                }
            });

            var result = r.login({}, () => {
                resolve(result)
                sessionStorage.clear() // Clear storage
            }, (error) => {
                console.log(error.data)
                reject(error.data)
            })
        });
    }

    resetPassword(username, password, new_password) {
        return new Promise((resolve, reject) => {
            let credentials = {
                "username": username,
                "password": password,
                "new_password": new_password,
            }
            var r = this.resource(`/api/v1/users/actions/changepassword/`, {}, {
                reset: {
                    method: "POST",
                }
            });

            var result = r.reset(credentials, () => {
                resolve(result)
            }, (error) => {
                console.log(error.data)
                reject(error.data)
            })
        })
    }
}

export default LoginResource;
