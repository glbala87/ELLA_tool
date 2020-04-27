import thenBy from 'thenby'
import { formatInheritance } from './genepanel'

export default function processAlleles(alleles, genepanel = null) {
    for (let allele of alleles) {
        if (allele.annotation.filtered_transcripts.length) {
            allele.annotation.filtered = allele.annotation.filtered_transcripts.map((t) =>
                allele.annotation.transcripts.find(
                    (anno_transcript) => anno_transcript.transcript === t
                )
            )
        } else {
            allele.annotation.filtered = allele.annotation.transcripts.sort(thenBy('transcript'))
        }

        allele.urls = getUrls(allele)
        allele.formatted = getFormatted(allele, genepanel)
        allele.links = getLinks(allele, genepanel)
    }

    return alleles
}

function getUrls(allele) {
    let urls = {
        exac: `http://exac.broadinstitute.org/variant/${allele.chromosome}-${allele.vcf_pos}-${allele.vcf_ref}-${allele.vcf_alt}`,
        '1000g': `http://browser.1000genomes.org/Homo_sapiens/Location/View?db=core;r=${
            allele.chromosome
        }:${allele.start_position + 1}-${allele.open_end_position}`,
        ensembl: `http://grch37.ensembl.org/Homo_sapiens/Location/View?r=${
            allele.chromosome
        }%3A${allele.start_position + 1}-${allele.open_end_position}`
    }

    if (
        allele.annotation.frequencies &&
        ('GNOMAD_EXOMES' in allele.annotation.frequencies ||
            'GNOMAD_GENOMES' in allele.annotation.frequencies)
    ) {
        urls.gnomad = `http://gnomad.broadinstitute.org/variant/${allele.chromosome}-${allele.vcf_pos}-${allele.vcf_ref}-${allele.vcf_alt}`
    } else {
        urls.gnomad = `http://gnomad.broadinstitute.org/region/${
            allele.chromosome
        }-${allele.vcf_pos - 10}-${allele.open_end_position + 10}`
    }

    if (
        allele.annotation.external &&
        'HGMD' in allele.annotation.external &&
        'acc_num' in allele.annotation.external.HGMD
    ) {
        urls.hgmd = `https://my.qiagendigitalinsights.com/bbp/view/hgmd/pro/mut.php?acc=${allele.annotation.external.HGMD.acc_num}`
    } else {
        const gene_symbols = allele.annotation.transcripts
            .filter((t) => allele.annotation.filtered_transcripts.indexOf(t.transcript) > -1)
            .map((t) => t.symbol)
        if (gene_symbols.length) {
            // HGMD only support one gene symbol for specific search
            const gene_symbol = gene_symbols[0]
            urls.hgmd = `https://my.qiagendigitalinsights.com/bbp/view/hgmd/pro/gene.php?gene=${gene_symbol}`
        }
    }

    if (allele.annotation.external && 'CLINVAR' in allele.annotation.external) {
        urls.clinvar = `https://www.ncbi.nlm.nih.gov/clinvar/variation/${allele.annotation.external.CLINVAR.variant_id}`
    } else {
        urls.clinvar = `https://www.ncbi.nlm.nih.gov/clinvar/?term=${
            allele.chromosome
        }[chr]%E2%80%8C+AND+${allele.vcf_pos - 10}:${allele.open_end_position + 10}[chrpos37]`
    }

    return urls
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
