import thenBy from 'thenby'
import { Compute } from 'cerebral'
import { state, props, string } from 'cerebral/tags'

export default function sortedAlleles(alleles) {
    return Compute(alleles, (alleles) => {
        if (alleles) {
            alleles = alleles.slice()
            alleles.sort(
                thenBy((a) => a.priority, -1)
                    .thenBy((a) => {
                        // Ignore seconds/milliseconds when sorting
                        let d = new Date(a.oldest_analysis)
                        d.setSeconds(0, 0)
                        return d.toISOString()
                    })
                    .thenBy((a) => a.allele.annotation.filtered[0].symbol)
                    .thenBy((a) => {
                        if (a.allele.annotation.filtered[0].strand > 0) {
                            return a.allele.start_position
                        }
                        return -a.allele.start_position
                    })
                    // It happens that alleles have same position, but different variations
                    .thenBy((a) => a.allele.annotation.filtered[0].HGVSc || 0)
            )
            return alleles
        }
        return []
    })
}
