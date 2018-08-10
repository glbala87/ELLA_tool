/* jshint esnext: true */

import { Service, Inject } from '../ng-decorators'

@Service({
    serviceName: 'User'
})
@Inject('$resource')
class UserService {
    constructor(resource) {
        this.user = null
    }

    hasUser() {
        return this.user !== null
    }

    getCurrentUserId() {
        if (this.hasUser()) {
            return this.user.id
        }

        return undefined
    }

    getCurrentUser() {
        if (this.hasUser()) {
            return this.user
        }
        return this.user
    }

    setCurrentUser(user) {
        this.user = user
        sessionStorage.clear() // Clear session storage when user changes
    }
}

export default UserService
