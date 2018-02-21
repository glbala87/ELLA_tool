import { formatInheritance } from './genepanel'

export default function processAlleles(alleles, genepanel = null) {
    for (let allele of alleles) {
        if (allele.annotation.filtered_transcripts.length) {
            allele.annotation.filtered = allele.annotation.transcripts.filter(anno =>
                allele.annotation.filtered_transcripts.includes(anno.transcript)
            )
        } else {
            allele.annotation.filtered = allele.annotation.transcripts
        }

        allele.urls = getUrls(allele)
        allele.formatted = getFormatted(allele, genepanel)
        allele.links = getLinks(allele, genepanel)
    }
}

function getUrls(allele) {
    let urls = {
        exac: `http://exac.broadinstitute.org/variant/${allele.chromosome}-${allele.vcf_pos}-${
            allele.vcf_ref
        }-${allele.vcf_alt}`,
        '1000g': `http://browser.1000genomes.org/Homo_sapiens/Location/View?db=core;r=${
            allele.chromosome
        }:${allele.start_position + 1}-${allele.open_end_position}`,
        ensembl: `http://grch37.ensembl.org/Homo_sapiens/Location/View?r=${
            allele.chromosome
        }%3A${allele.start_position + 1}-${allele.open_end_position}`
    }

    if ('HGMD' in allele.annotation.external && 'acc_num' in allele.annotation.external.HGMD) {
        urls.hgmd = `https://portal.biobase-international.com/hgmd/pro/mut.php?accession=${
            allele.annotation.external.HGMD.acc_num
        }`
    }

    if ('CLINVAR' in allele.annotation.external) {
        urls.clinvar = `https://www.ncbi.nlm.nih.gov/clinvar/variation/${
            allele.annotation.external.CLINVAR.variant_id
        }`
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
    // genotype
    //
    if ('samples' in allele) {
        if (allele.samples.length > 1) {
            // If multiple, return 'S: A/T, H: A/G'
            formatted.genotype = allele.samples
                .map(s => {
                    return s.sample_type.substring(0, 1).toUpperCase() + ': ' + s.genotype.genotype
                })
                .join(', ')
        } else {
            formatted.genotype = allele.samples[0].genotype.genotype
        }
    } else {
        formatted.genotype = ''
    }

    //
    // HGVSg / alamut
    //
    // (Alamut also support dup, but we treat them as indels)
    // (dup: Chr13(GRCh37):g.32912008_3291212dup )

    // Database is 0-based, hgvsg uses 1-based index
    let start = allele.start_position
    let end = allele.open_end_position

    if (allele.change_type === 'SNP') {
        // snp: g.66285951C>Tdel:
        formatted.hgvsg = `g.${start + 1}${allele.change_from}>${allele.change_to}`
    } else if (allele.change_type === 'del') {
        // del: g.32912008_32912011del
        formatted.hgvsg = `g.${start + 1}_${end}del`
    } else if (allele.change_type === 'ins') {
        // ins: g.32912008_3291209insCGT
        formatted.hgvsg = `g.${start}_${start + 1}ins${allele.change_to}`
    } else if (allele.change_type === 'indel') {
        // delins: g.32912008_32912011delinsGGG
        formatted.hgvsg = `g.${start + 1}_${end}delins${allele.change_to}`
    } else {
        // edge case, shouldn't happen, but this is valid format as well
        formatted.hgvsg = `g.${start + 1}`
    }
    formatted.alamut = `Chr${allele.chromosome}(${allele.genome_reference}):${formatted.hgvsg}`

    //
    // genomic position
    //
    if (allele.change_type === 'SNP') {
        formatted.genomicPosition = `${allele.chromosome}:${allele.start_position + 1}`
    } else if (allele.change_type === 'del') {
        if (allele.change_from.length > 1) {
            formatted.genomicPosition = `${allele.chromosome}:${allele.start_position + 1}-${
                allele.open_end_position
            }`
        } else {
            formatted.genomicPosition = `${allele.chromosome}:${allele.start_position + 1}`
        }
    } else if (allele.change_type === 'ins') {
        formatted.genomicPosition = `${allele.chromosome}:${
            allele.start_position
        }-${allele.start_position + 1}`
    } else {
        formatted.genomicPosition = `${allele.chromosome}:${allele.start_position + 1}-${
            allele.open_end_position
        }`
    }

    //
    // sample type
    //
    if (allele.samples) {
        formatted.sampleType = allele.samples
            .map(s => s.sample_type.substring(0, 1))
            .join('')
            .toUpperCase()
    }

    //
    // inheritance
    //
    if (genepanel) {
        let inheritance = allele.annotation.filtered.map(a => {
            return formatInheritance(genepanel, a.symbol)
        })
        formatted.inheritance = inheritance.join(' | ')

        formatted.hgvsc = allele.annotation.filtered
            .map(a => {
                return `${a.symbol} ${a.HGVSc}`
            })
            .join('; ')
    }

    return formatted
}
