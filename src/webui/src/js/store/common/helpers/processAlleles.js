import thenBy from 'thenby'

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
    let start = allele.start_position + 1
    let end = allele.open_end_position
    // converting to 1 based index, closed system.
    // vcf defined cnv END: POS + length(REF allele) - 1
    let cnvEnd = start + allele.length - 1

    switch (allele.change_type) {
        case 'SNP':
            formatted.genomicPosition = `${allele.chromosome}:${start}`
            formatted.hgvsg = `g.${start}${allele.change_from}>${allele.change_to}`
            break
        case 'del':
            if (start === end) {
                formatted.hgvsg = `g.${start}del`
                formatted.genomicPosition = `${allele.chromosome}:${start}`
            } else {
                formatted.hgvsg = `g.${start}_${end}del`
                formatted.genomicPosition = `${allele.chromosome}:${start}-${end}`
            }
            break
        case 'indel':
            if (start === end) {
                formatted.hgvsg = `g.${start}delins${allele.change_to}`
                formatted.genomicPosition = `${allele.chromosome}:${start}`
            } else {
                formatted.hgvsg = `g.${start}_${end}delins${allele.change_to}`
                formatted.genomicPosition = `${allele.chromosome}:${start}-${end}`
            }
            break
        case 'ins':
            formatted.hgvsg = `g.${start}_${end + 1}ins${allele.change_to}`
            formatted.genomicPosition = `${allele.chromosome}:${start}-${end + 1}`
            break
        case 'dup':
            formatted.hgvsg = `g.${start}_${cnvEnd}dup`
            formatted.genomicPosition = `${allele.chromosome}:${start}-${cnvEnd}`
            break
        case 'dup_tandem':
            formatted.hgvsg = `g.${start}_${cnvEnd}dup_tandem`
            formatted.genomicPosition = `${allele.chromosome}:${start}-${cnvEnd}`
            break
        case 'del_me':
            formatted.hgvsg = `g.${start}_${length}del_me`
            formatted.genomicPosition = `${allele.chromosome}:${start}-${end}`
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
        let inheritance = allele.annotation.filtered.map((a) =>
            genepanel.inheritances
                .filter((i) => i.hgnc_id === a.hgnc_id)
                .map((inh) => inh.inheritance)
        )
        formatted.inheritance = [...new Set(inheritance.flat())].join(' | ')
    }

    return formatted
}
