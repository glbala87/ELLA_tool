/* jshint esnext: true */

import {Directive, Inject} from '../ng-decorators';

@Directive({
    selector: 'user-dashboard',
    templateUrl: 'ngtmpl/userDashboard.ngtmpl.html'
})
@Inject('$scope', '$timeout', '$location', 'Config', 'User', 'Navbar', 'OverviewResource', 'LoginResource', 'toastr')
export class UserDashboardController {
    constructor($scope, $timeout, location, Config, User, Navbar, OverviewResource, LoginResource, toastr) {
        this.location = location;
        this.timeout = $timeout;
        this.user = User;
        this.usersInGroup = [];
        
        this.user.getAll().then(d => {
            this.usersInGroup = d.filter(r => this.user.user.id !== r.id);
        });
        
        this.users = [];
        this.overviewResource = OverviewResource;
        this.loginResource = LoginResource;
        this.toastr = toastr;
        this.config = Config.getConfig();

        Navbar.clearItems();

        this.overviewResource.getActivities().then(d => {
            this.activity_stream = d;
        });

        this.overviewResource.getUserStats().then(d => {
            this.user_stats = d;
        });
    }

    logout() {
        this.toastr.info('Logging out...', '', {timeOut: 1000});
        this.timeout(() => {
                this.loginResource.logout().then(a => {
                this.location.path('/login');
            });
        }, 1000);

    }

    getActivityStartAction(item) {
        let actions = {
            started: 'started analysing',
            started_review: 'started reviewing',
            review: 'reviewed'
        };
        if (item.start_action in actions) {
            return actions[item.start_action];
        }
        return 'unknown';
    }

    getActivityEndAction(item) {
        let actions = {
            finalized: ' and finalized it',
            marked_review: ' and marked it for review'
        };
        if (item.end_action in actions) {
            return actions[item.end_action];
        }
        return '';
    }

    getActivityName(item) {
        if ('allele' in item) {
            return item.allele.toString();
        }
        if ('analysis' in item) {
            return item.analysis.name;
        }
    }

    getActivityUser(item) {
        if (this.isUserAction(item)) {
            return 'You';
        }
        return item.user.full_name;

    }

    getActivityUrl(item) {
        if (item.allele) {
            return item.allele.getWorkflowUrl(item.genepanel);
        }
        if (item.analysis) {
            return `/analyses/${item.analysis.id}`
        }
    }

    isUserAction(item) {
        return item.user.id == this.user.getCurrentUserId()
    }
}
