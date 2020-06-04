import { Compute } from 'cerebral'
import { state } from 'cerebral/tags'
import {
    formatInheritance,
    getOmimEntryId,
    findGeneConfigOverride
} from '../../common/helpers/genepanel'

/**
 * Calculates various genepanel information for every gene
 * found in the filtered transcripts for given allele.
 * Returns an object with values per gene.
 * @param {state} genepanel Genepanel tag
 * @param {state} allele Allele tag
 */
export default (hgncId, genepanel, hgncSymbolFallback) => {
    return Compute(
        hgncId,
        genepanel,
        state`app.config.user.user_config.acmg`,
        hgncSymbolFallback,

        (hgncId, genepanel, acmgConfig, hgncSymbolFallback) => {
            const result = {}

            const props = ['last_exon_important', 'disease_mode']
            const geneConfigOverride = findGeneConfigOverride(hgncId, acmgConfig)
            for (let p of props) {
                result[p] = {
                    value: p in geneConfigOverride ? geneConfigOverride[p] : acmgConfig[p],
                    overridden: p in geneConfigOverride
                }
            }

            result.inheritance = formatInheritance(hgncId, genepanel, hgncSymbolFallback)

            // If 'frequency' is defined for the gene, use that.
            // Otherwise, use the default given the inheritance key
            if ('frequency' in geneConfigOverride) {
                result.freqCutoffs = {
                    value: geneConfigOverride.frequency.thresholds,
                    overridden: true
                }
            } else {
                result.freqCutoffs = {
                    value:
                        result.inheritance === 'AD'
                            ? acmgConfig.frequency.thresholds['AD']
                            : acmgConfig.frequency.thresholds['default'],
                    overridden: false
                }
            }

            if ('comment' in geneConfigOverride) {
                result.comment = geneConfigOverride['comment']
            }
            result.omimEntryId = getOmimEntryId(hgncId, genepanel, hgncSymbolFallback)
            result.phenotypes = genepanel.phenotypes.filter(
                (p) => p.gene.hgnc_id === hgncId || p.gene.hgnc_symbol === hgncSymbolFallback
            )
            return result
        }
    )
}
