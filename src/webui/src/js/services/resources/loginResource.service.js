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

    login(user_id, password) {
        return new Promise((resolve, reject) => {
            var r = this.resource(`/api/v1/users/${user_id}/${password}`, {}, {
                login: {
                    isArray: false
                }
            });
            var result = r.login( () => {
                resolve(result)
            }, reject)
        });
    }
    //
    // get(query) {
    //     return new Promise((resolve, reject) => {
    //         var r = this.resource(`/api/v1/search/?q=${encodeURIComponent(query)}`, {}, {
    //             get: {
    //                 isArray: false
    //             }
    //         });
    //         var result = r.get(function () {
    //             for (let item of result.alleles) {
    //                 let alleles = [];
    //                 for (let a of item.alleles) {
    //                     alleles.push(new Allele(a));
    //                 }
    //                 item.alleles = alleles;
    //             }
    //             for (let item of result.alleleassessments) {
    //                 let aa = [];
    //                 for (let a of item.alleles) {
    //                     aa.push(new Allele(a));
    //                 }
    //                 item.alleles = aa;
    //             }
    //             let analyses = [];
    //             for (let a of result.analyses) {
    //                 analyses.push(new Analysis(a));
    //             }
    //             result.analyses = analyses;
    //             resolve(result);
    //         }, reject);
    //     });
    // }
}

export default LoginResource;
