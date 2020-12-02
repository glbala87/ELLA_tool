import thenBy from 'thenby'
import { Compute } from 'cerebral'

export default function sortedAlleles(alleles) {
    return Compute(alleles, (alleles) => {
        if (alleles) {
            alleles = alleles.slice()
            alleles.sort(
                thenBy((a) => a.priority, -1)
                    .thenBy((a) => {
                        // Ignore seconds/milliseconds when sorting
                        let d = new Date(a.date_created)
                        d.setSeconds(0, 0)
                        return d.toISOString()
                    })
                    .thenBy((a) => {
                        if (
                            a.allele.annotation.hasOwnProperty('filtered') &&
                            a.allele.annotation.filtered.length > 0 &&
                            a.allele.annotation.filtered[0].hasOwnProperty('symbol')
                        )
                            a.allele.annotation.filtered[0].symbol
                        else 0
                    })
                    .thenBy((a) => {
                        if (
                            a.allele.annotation.hasOwnProperty('filtered') &&
                            a.allele.annotation.filtered.length > 0 &&
                            a.allele.annotation.filtered[0].hasOwnProperty('strand')
                        ) {
                            if (a.allele.annotation.filtered[0].strand > 0) {
                                return a.allele.start_position
                            }
                            return -a.allele.start_position
                        } else 0
                    })
                    // It happens that alleles have same position, but different variations
                    .thenBy((a) => {
                        if (
                            a.allele.annotation.hasOwnProperty('filtered') &&
                            a.allele.annotation.filtered.length > 0 &&
                            a.allele.annotation.filtered[0].hasOwnProperty('HGVsc')
                        )
                            a.allele.annotation.filtered[0].HGVSc
                        else 0
                    })
            )
            return alleles
        }
        return []
    })
}
