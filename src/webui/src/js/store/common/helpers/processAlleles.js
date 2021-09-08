import thenBy from 'thenby'
import { formatInheritance } from './genepanel'

/**
 *  Troubleshooting:
 *
 * This seems to be called with alleles not containing annoation, I
 * see two possibilities:
 *
 * 1. There is no annotation data, but this worked before the major
 *    refactoring, so may not be the cause, alternatively something wasn't
 *    properly tested previously.
 * 2. There is something wrong in this workflow test. Could be related
 *    to the filter modal, but it is hard to see the correlation between
 *    that and annotion. Might be some forgiving undefined value in Javascript,
 *    but still, this should have crashed in the state store.
 *
 * There seemes to be multiple paths to filteredAlleles in the cerebral store
 * active in the workflows.modals.addExcludedAlleles and other places.
 *
 * The loadExcludedAlleles seems to be initiated from multiple places,
 * we need a way to assure that we then load the filteredAlleles based
 * upon the caller type.
 *
 * Excluded alleles and Filtered alleles is the same concept or not?
 *
 * This is confusing for sure...
 *
 */

export default function processAlleles(alleles, genepanel = null) {
    for (let allele of alleles) {
        if (allele.annotation.filtered_transcripts.length) {
            allele.annotation.filtered = allele.annotation.filtered_transcripts.map((t) =>
                allele.annotation.transcripts.find(
                    (anno_transcript) => anno_transcript.transcript === t
                )
            )
        } else {
            if ('transcripts' in allele.annotation) {
                allele.annotation.filtered = allele.annotation.transcripts.sort(
                    thenBy('transcript')
                )
            } else {
                allele.annotation.transcripts = []
                allele.annotation.filtered = []
            }
        }

        allele.formatted = getFormatted(allele, genepanel)
        allele.links = getLinks(allele, genepanel)
    }

    return alleles
}

function getLinks(allele, genepanel) {
    let links = {}
    if (genepanel) {
        links.workflow =
            `/workflows/variants/${allele.genome_reference}/` +
            `${allele.chromosome}-${allele.vcf_pos}-${allele.vcf_ref}-${allele.vcf_alt}` +
            `?gp_name=${genepanel.name}&gp_version=${genepanel.version}&allele_id=${allele.id}`
    } else {
        links.workflow =
            `/workflows/variants/${allele.genome_reference}/` +
            `${allele.chromosome}-${allele.vcf_pos}-${allele.vcf_ref}-${allele.vcf_alt}` +
            `?allele_id=${allele.id}`
    }

    return links
}

function getFormatted(allele, genepanel) {
    let formatted = {}

    //
    // HGVSg / alamut
    //
    // (Alamut also support dup, but we treat them as indels)
    // (dup: Chr13(GRCh37):g.32912008_3291212dup )

    // Database is 0-based, hgvsg uses 1-based index
    let start = allele.start_position
    let end = allele.open_end_position
    let cnvEnd = start + 1 + allele.length

    switch (allele.change_type) {
        case 'SNP':
            formatted.genomicPosition = `${allele.chromosome}:${start + 1}`
            formatted.hgvsg = `g.${start + 1}${allele.change_from}>${allele.change_to}`
            break
        case 'del':
            if (start + 1 === end) {
                formatted.hgvsg = `g.${start + 1}del`
                formatted.genomicPosition = `${allele.chromosome}:${start + 1}`
            } else {
                formatted.hgvsg = `g.${start + 1}_${end}del`
                formatted.genomicPosition = `${allele.chromosome}:${start + 1}-${end}`
            }
            break
        case 'indel':
            if (start + 1 === end) {
                formatted.hgvsg = `g.${start + 1}delins${allele.change_to}`
                formatted.genomicPosition = `${allele.chromosome}:${start + 1}`
            } else {
                formatted.hgvsg = `g.${start + 1}_${end}delins${allele.change_to}`
                formatted.genomicPosition = `${allele.chromosome}:${start + 1}-${end}`
            }
            break
        case 'ins':
            formatted.hgvsg = `g.${start + 1}_${end + 1}ins${allele.change_to}`
            formatted.genomicPosition = `${allele.chromosome}:${start + 1}-${end + 1}`
            break
        case 'dup':
            formatted.hgvsg = `g.${start + 1}_${cnvEnd}dup`
            formatted.genomicPosition = `${allele.chromosome}:${start + 1}-${cnvEnd}`
            break
        case 'dup_tandem':
            formatted.hgvsg = `g.${start + 1}_${cnvEnd}dup_tandem`
            formatted.genomicPosition = `${allele.chromosome}:${start + 1}-${cnvEnd}`
            break
        case 'del_me':
            formatted.hgvsg = `g.${start + 1}_${length}del_me`
            formatted.genomicPosition = `${allele.chromosome}:${start + 1}-${end}`
            break
        default:
            throw Error(`Unsupported change type detected (${allele.id}): ${allele.change_type}`)
    }

    formatted.alamut = `Chr${allele.chromosome}(${allele.genome_reference}):${formatted.hgvsg}`

    //
    // hgvsc
    //

    if (allele.annotation.filtered.length) {
        const includeTranscript = allele.annotation.filtered.length > 1
        formatted.display = allele.annotation.filtered
            .map((a) => {
                return `${a.symbol} ${includeTranscript ? a.transcript + ' ' : ''}${
                    a.HGVSc ? a.HGVSc : formatted.hgvsg
                }${a.HGVSp ? ' (' + a.HGVSp + ')' : ''}`
            })
            .join('; ')
    }

    //
    // sample type
    //
    if (allele.samples) {
        formatted.sampleType = allele.samples
            .map((s) => s.sample_type.substring(0, 1))
            .join('')
            .toUpperCase()
    }

    //
    // inheritance
    //
    if (genepanel) {
        let inheritance = allele.annotation.filtered.map((a) => {
            return formatInheritance(a.hgnc_id, genepanel)
        })
        formatted.inheritance = inheritance.join(' | ')
    }

    return formatted
}
