import { Compute } from 'cerebral'
import { state } from 'cerebral/tags'
import {
    formatInheritance,
    getOmimEntryId,
    findGeneConfigOverride
} from '../../common/helpers/genepanel'

/**
 * Calculates various genepanel information for every gene
 * found in the gene panel.
 * Returns an object with values per gene.
 * @param {state} genepanel Genepanel tag
 * @param {state} allele Allele tag
 */
export default (genepanel) => {
    return Compute(genepanel, state`app.config.user.user_config.acmg`, (genepanel, acmgConfig) => {
        const result = {}

        const uniqueHgncIds = new Set(genepanel.transcripts.map((t) => t.gene.hgnc_id))
        for (let hgncId of uniqueHgncIds) {
            result[hgncId] = {}

            const props = ['last_exon_important', 'disease_mode']
            const geneConfigOverride = findGeneConfigOverride(hgncId, acmgConfig)
            for (let p of props) {
                result[hgncId][p] = {
                    value: p in geneConfigOverride ? geneConfigOverride[p] : acmgConfig[p],
                    overridden: p in geneConfigOverride
                }
            }
            result[hgncId].inheritance = formatInheritance(hgncId, genepanel)

            // If 'frequency' is defined for the gene, use that.
            // Otherwise, use the default given the inheritance key
            if ('frequency' in geneConfigOverride) {
                result[hgncId].freqCutoffs = {
                    value: geneConfigOverride.frequency.thresholds,
                    overridden: true
                }
            } else {
                result[hgncId].freqCutoffs = {
                    value:
                        result[hgncId].inheritance === 'AD'
                            ? acmgConfig.frequency.thresholds['AD']
                            : acmgConfig.frequency.thresholds['default'],
                    overridden: false
                }
            }

            result[hgncId].omimEntryId = getOmimEntryId(hgncId, genepanel)
            result[hgncId].phenotypes = genepanel.phenotypes.filter(
                (p) => p.gene.hgnc_id === hgncId
            )
        }
        return result
    })
}
