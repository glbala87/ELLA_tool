import { Compute } from 'cerebral'

export default (urlTemplate, allele) =>
    Compute(urlTemplate, allele, (urlTemplate, allele) => {
        // Replace ${expressions} (etc) with ${map.expressions}.
        var sanitized = urlTemplate
            .replace(/\$\{([\s]*[^;\{]+[\s]*)\}/g, function(_, match) {
                return `\$\{map.${match.trim()}\}`
            })
            // Afterwards, replace anything that's not ${map.expressions}' (etc) with a blank string.
            .replace(/(\$\{(?!map\.)[^}]+\})/g, '')
        const templateStringFn = Function('map', `return \`${sanitized}\``)
        try {
            const r = templateStringFn({ allele })
            return r
        } catch (err) {
            return urlTemplate
        }
    })
