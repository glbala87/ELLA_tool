/* jshint esnext: true */

import {Directive, Inject} from '../../ng-decorators';


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
        analysis: '=',
        allele: '=',
        references: '=',
        alleleState: '=',
        onSave: '&?',
        boxes: '=',  // Array of objects.
        boxesOptions: '='
    },
    link: (scope, elem, attrs, ctrl) => {

        // Dynamically create the html for the content-boxes
        let html = '';
        if (scope.boxes) {
            for (let box of scope.boxes) {
                let classes = '';
                let attrs = '';
                if ('class' in box) {
                    classes = box.class.join(' ');
                }

                if ('attr' in box) {
                    for (let [k, v] of Object.entries(box.attr)) {
                        attrs += `${k}="${v}"`;
                    }
                }

                let on_save = '';
                if (scope.vm.onSave) {
                    on_save = 'on-save="vm.onSave()"';
                }


                let options = '';
                let cb_options = '';
                if (scope.vm.boxesOptions &&
                    box.tag in scope.vm.boxesOptions) {
                    options = `options="vm.boxesOptions['${box.tag}']"`;
                    cb_options = `cb-options="vm.boxesOptions['${box.tag}']"`
                }
                html += `
                <contentbox ${options}>
                  <cbbody>
                    <${box.tag}
                        class="cb-wrapper"
                        analysis="vm.analysis"
                        allele="vm.allele"
                        references="vm.references"
                        allele-state="vm.alleleState"
                        ${cb_options}
                        ${on_save}
                        ${attrs}
                    ></${box.tag}>
                  </cbbody>
                </contentbox>`;
            }
            let compiled = scope.vm.compile(html)(scope);
            elem.append(compiled);
        }
    }

})
@Inject(
    'Config',
    '$compile'
)
export class AlleleSectionboxContentController {


    constructor(Config,
                $compile) {
        this.config = Config.getConfig();
        this.compile = $compile;
    }

}
