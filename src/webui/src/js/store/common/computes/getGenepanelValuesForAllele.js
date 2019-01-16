import { Compute } from 'cerebral'
import { state } from 'cerebral/tags'
import {
    getInheritanceCodes,
    getOmimEntryId,
    findGeneConfigOverride,
    phenotypesBy
} from '../../common/helpers/genepanel'

/**
 * Calculates various genepanel information for every gene
 * found in the filtered transcripts for given allele.
 * Returns an object with values per gene.
 * @param {state} genepanel Genepanel tag
 * @param {state} allele Allele tag
 */
export default (genepanel, allele) => {
    return Compute(
        genepanel,
        allele,
        state`app.config.user.user_config.acmg`,
        (genepanel, allele, acmgConfig, get) => {
            const result = {}
            if (!allele) {
                return result
            }
            const genes = allele.annotation.filtered.map((t) => [t.hgnc_id, t.symbol])
            for (const [hgncId, symbol] of genes) {
                if (symbol in result) {
                    continue
                }
                result[symbol] = {
                    _overridden: [] // Holds keys that are overridden by genepanel config.
                }
                const props = ['last_exon_important', 'disease_mode', 'frequency']
                const geneConfigOverride = findGeneConfigOverride(hgncId, acmgConfig)
                for (let p of props) {
                    if (p in geneConfigOverride) {
                        result[symbol][p] = geneConfigOverride[p]
                        if (p === 'frequency') {
                            result[symbol]['_overridden'].push('freq_cutoffs_external')
                            result[symbol]['_overridden'].push('freq_cutoffs_internal')
                        } else {
                            result[symbol]['_overridden'].push(p)
                        }
                    } else {
                        result[symbol][p] = acmgConfig[p]
                    }
                }

                const inheritance = getInheritanceCodes(symbol, genepanel)
                result[symbol]['inheritance'] = inheritance

                // If 'frequency' is defined for the gene, use that.
                // Otherwise, use the default given the inheritance key
                if ('frequency' in geneConfigOverride) {
                    result[symbol]['freq_cutoffs'] = geneConfigOverride.frequency.thresholds
                } else {
                    if (inheritance === 'AD') {
                        result[symbol]['freq_cutoffs'] = acmgConfig.frequency.thresholds['AD']
                    } else {
                        result[symbol]['freq_cutoffs'] = acmgConfig.frequency.thresholds['default']
                    }
                }

                if ('comment' in geneConfigOverride) {
                    result[symbol]['comment'] = geneConfigOverride['comment']
                }
                result[symbol]['omim_entry_id'] = getOmimEntryId(symbol, genepanel)
                result[symbol]['phenotypes'] = phenotypesBy(symbol, genepanel)
            }
            return result
        }
    )
}
