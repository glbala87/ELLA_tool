/* jshint esnext: true */

import { Directive, Inject } from '../ng-decorators'

import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'

app.component('navbar', {
    templateUrl: 'ngtmpl/navbar-new.ngtmpl.html',
    controller: connect(
        {
            config: state`app.config`,
            user: state`app.user`,
            currentView: state`views.current`,
            title: state`app.navbar.title`
            //optionsSearchChanged: signal`search.optionsSearchChanged`,
        },
        'Navbar'
    )
})

@Directive({
    selector: 'navbar-old',
    templateUrl: 'ngtmpl/navbar.ngtmpl.html'
})
@Inject('Navbar', 'User', 'Config', '$location')
export class NavbarController {
    constructor(Navbar, User, Config, $location) {
        this.navbarService = Navbar
        this.user = User
        this.config = Config.getConfig()
        this.location = $location
    }

    hasAllele() {
        return Boolean(this.navbarService.getAllele())
    }

    getAllele() {
        return this.navbarService.getAllele()
    }

    getGenepanel() {
        return this.navbarService.getGenepanel()
    }

    getItems() {
        return this.navbarService.getItems()
    }

    isLastItem(item) {
        let idx = this.navbarService.getItems().indexOf(item)
        return idx === this.navbarService.getItems().length - 1
    }

    hasUrl(item) {
        if (item.url) {
            return true
        } else {
            return false
        }
    }

    isLogin() {
        return this.location.path() == '/login'
    }
}
