import { Compute } from 'cerebral'
import { state, props, string } from 'cerebral/tags'
import {
    getInheritanceCodes,
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
export default (genepanel, allele) => {
    return Compute(
        genepanel,
        allele,
        state`app.config.variant_criteria.genepanel_config`,
        (genepanel, allele, globalConfig, get) => {
            const result = {}
            if (!allele) {
                return result
            }
            const symbols = [...new Set(allele.annotation.filtered.map(t => t.symbol))]
            for (const symbol of symbols) {
                result[symbol] = {
                    _overridden: [] // Holds keys that are overridden by genepanel config.
                }
                let props = ['last_exon_important', 'disease_mode', 'freq_cutoffs']
                let config_override = findGeneConfigOverride(symbol, genepanel.config)
                for (let p of props) {
                    if (p in config_override) {
                        result[symbol][p] = config_override[p]
                        if (p === 'freq_cutoffs') {
                            result[symbol]['_overridden'].push('freq_cutoffs_external')
                            result[symbol]['_overridden'].push('freq_cutoffs_internal')
                        } else {
                            result[symbol]['_overridden'].push(p)
                        }
                    } else {
                        result[symbol][p] = globalConfig[p]
                    }
                }

                const inheritance = getInheritanceCodes(symbol, genepanel)
                result[symbol]['inheritance'] = inheritance

                // If 'freq_cutoffs' is defined in genepanel config, use those. Otherwise, use the default
                // given the inheritance key
                if (!('freq_cutoffs' in config_override)) {
                    if (inheritance == 'AD') {
                        result[symbol]['freq_cutoffs'] = globalConfig['freq_cutoff_groups']['AD']
                    } else {
                        result[symbol]['freq_cutoffs'] =
                            globalConfig['freq_cutoff_groups']['default']
                    }
                }

                if ('comment' in config_override) {
                    result[symbol]['comment'] = config_override['comment']
                }
                result[symbol]['omim_entry_id'] = getOmimEntryId(symbol, genepanel)
            }
            return result
        }
    )
}
