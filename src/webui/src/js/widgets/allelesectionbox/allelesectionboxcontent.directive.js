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
    link: (scope, elem) => {
        // Dynamically create the html for the content-boxes
        // Watch required to handle different boxes, determined in part by annotation config
        scope.$watch(
            () => scope.boxes,
            () => {
                let html = ''
                elem.empty()
                if (scope.boxes) {
                    for (let box of scope.boxes) {
                        let classes = ['cb-wrapper']
                        let attrs = ''

                        if ('class' in box) {
                            classes = classes.concat(box.class)
                        }
                        if ('attr' in box) {
                            for (let [k, v] of Object.entries(box.attr)) {
                                attrs += ` ${k}="${v}"`
                            }
                        }

                        // If title not specified in config, use the source (if available)
                        // Split source on '.', and take the last element (e.g. "external.spliceai" -> "spliceai")
                        let title = box.title
                        if (!title && 'source' in box) {
                            title = box.source.split(/\./).pop()
                        }
                        const url = box.url ? ` url="${box.url}"` : ''
                        const url_empty = box.url_empty ? ` url-empty="${box.url_empty}"` : ''
                        html += `
                        <${box.tag}
                            class="${classes.join(' ')}"
                            allele-path="vm.allelePath"
                            source="${box.source}"
                            box-title="${title}"
                            annotation-config-id="${box.annotationConfigId}"
                            annotation-config-item-idx="${box.annotationConfigItemIdx}"
                            ${attrs}
                            ${url}
                            ${url_empty}
                        ></${box.tag}>`
                    }
                    if (html) {
                        let compiled = scope.vm.compile(html)(scope)
                        elem.append(compiled)
                    }
                }
            }
        )
    }
})
@Inject('Config', '$compile')
export class AlleleSectionboxContentController {
    constructor(Config, $compile) {
        this.config = Config.getConfig()
        this.compile = $compile
    }
}
