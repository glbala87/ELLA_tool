/* jshint esnext: true */
import toastr from 'toastr'
import copy from 'copy-to-clipboard'
import app from '../ng-decorators'
import { Compute } from 'cerebral'
import { state, props } from 'cerebral/tags'
import { connect } from '@cerebral/angularjs'

/**
 * Directive for supporting dynamically switching between normal
 * <a> open link behavior and copy-link-to-clipboard instead.
 */

// From https://gist.github.com/bryanerayner/68e1498d4b1b09a30ef6#file-generatetemplatestring-js
/**
 * Produces a function which uses template strings to do simple interpolation from objects.
 *
 * Usage:
 *    var makeMeKing = generateTemplateString('${name} is now the king of ${country}!');
 *
 *    console.log(makeMeKing({ name: 'Bryan', country: 'Scotland'}));
 *    // Logs 'Bryan is now the king of Scotland!'
 */
var generateTemplateString = (function() {
    var cache = {}

    function generateTemplate(template) {
        var fn = cache[template]

        if (!fn) {
            // Replace ${expressions} (etc) with ${map.expressions}.

            var sanitized = template
                .replace(/\$\{([\s]*[^;\{]+[\s]*)\}/g, function(_, match) {
                    return `\$\{map.${match.trim()}\}`
                })
                // Afterwards, replace anything that's not ${map.expressions}' (etc) with a blank string.
                .replace(/(\$\{(?!map\.)[^}]+\})/g, '')

            fn = Function('map', `return \`${sanitized}\``)
        }

        return fn
    }

    return generateTemplate
})()

const interpolatedUrl = Compute(
    props`href`,
    state`views.workflows.interpretation.data.alleles.${state`views.workflows.selectedAllele`}`,
    (url, allele) => {
        /** Interpolate urls from
         * https://.../${allele.chromosome}/${allele.annotation.external.CLINVAR.variant_id}/${allele.vcf_pos+10}
         * to
         * https://.../1/123456
         */
        url = url.replace(/\s/g, '')
        const templateString = generateTemplateString(url)
        return templateString({ allele })
    }
)

app.component('aClip', {
    bindings: {
        href: '@?',
        title: '@?',
        toClipboard: '=?'
    },
    transclude: true,
    template: `<span><a title="{{title}}" ng-if="::!$ctrl.shouldCopy()" ng-href="{{$ctrl.interpolatedUrl}}" target="{{$ctrl.interpolatedUrl}}" ng-transclude></a><a style="cursor: pointer;" ng-if="::$ctrl.shouldCopy()" title="{{title}}" ng-click="$ctrl.copyToClipboard()" ng-transclude></a></span>`,
    controller: connect(
        {
            interpolatedUrl,
            fallbackCopyToClipboard: state`app.config.app.links_to_clipboard`
        },
        'aClip',
        [
            '$scope',
            ($scope) => {
                const $ctrl = $scope.$ctrl
                Object.assign($ctrl, {
                    copyToClipboard() {
                        copy($ctrl.interpolatedUrl)
                        toastr.info('Copied link to clipboard.', null, 1000)
                        console.log(`Copied ${$ctrl.interpolatedUrl} to clipboard.`)
                    },
                    shouldCopy() {
                        return $ctrl.toClipboard !== undefined
                            ? $ctrl.toClipboard
                            : $ctrl.fallbackCopyToClipboard
                    }
                })
            }
        ]
    )
})
