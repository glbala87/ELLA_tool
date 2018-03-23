/* jshint esnext: true */

import { Directive, Inject } from '../../ng-decorators'

/**
 * Directive for dynamically creating boxes of content-boxes
 * in an <allele-card>. The template is dynamically created
 * from incoming configuration, before it's compiled and
 * appended onto the root element of this directive.
 *
 * 'boxes' example:
 *
 *     [
 *         {
 *         'title': 'ExAC',
 *         'tag': 'allele-info-frequency-exac',
 *         'class': ['some-class'],
 *         'attr': {
 *              'editable': 'true'
 *         }
 *     },
 *     {...}
 *     ]
 *
 */
@Directive({
    selector: 'allele-sectionbox-content',
    template: '',
    scope: {
        allelePath: '<',
        boxes: '=' // Array of objects.
    },
    link: (scope, elem, attrs, ctrl) => {
        // Dynamically create the html for the content-boxes
        let html = ''
        if (scope.boxes) {
            for (let box of scope.boxes) {
                let classes = ''
                let attrs = ''
                if ('class' in box) {
                    classes = box.class.join(' ')
                }

                if ('attr' in box) {
                    for (let [k, v] of Object.entries(box.attr)) {
                        attrs += `${k}="${v}"`
                    }
                }

                html += `
                <${box.tag}
                    class="cb-wrapper"
                    allele-path="vm.allelePath"
                    ${attrs}
                ></${box.tag}>`
            }
            let compiled = scope.vm.compile(html)(scope)
            elem.append(compiled)
        }
    }
})
@Inject('Config', '$compile')
export class AlleleSectionboxContentController {
    constructor(Config, $compile) {
        this.config = Config.getConfig()
        this.compile = $compile
    }
}
