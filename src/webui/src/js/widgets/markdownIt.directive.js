import markdownIt from 'markdown-it'
import { Directive, Inject } from '../ng-decorators'

@Directive({
    selector: 'markdown-it',
    template: '<div class="markdown"></div>',
    scope: {
        markdown: '='
    },
    link: (scope, elem, attrs) => {
        var md = markdownIt({ breaks: true })
        if (scope.markdown && scope.markdown.length) {
            elem.children()[0].innerHTML = md.render(scope.markdown)
        }
    }
})
@Inject('$sce')
export class MarkdownItController {
    constructor($sce) {
        this.sce = $sce
    }
}
