import markdownIt from 'markdown-it'
import { Directive, Inject } from '../ng-decorators'

import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'

app.component('markdownIt', {
    bindings: {
        markdown: '='
    },
    // transclude: true,
    template: '<div class="markdown" ng-bind-html="$ctrl.renderMarkdown()"></div>',
    controller: connect(
        {},
        'markdownIt',
        [
            '$scope',
            ($scope) => {
                const $ctrl = $scope.$ctrl
                const md = markdownIt({ breaks: true })
                Object.assign($ctrl, {
                    renderMarkdown: () => {
                        if ($ctrl.markdown && $ctrl.markdown.length) {
                            return md.render($ctrl.markdown)
                        } else {
                            return ''
                        }
                    }
                })
            }
        ]
    )
})
