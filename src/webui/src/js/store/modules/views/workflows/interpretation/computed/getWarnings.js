import { Compute } from 'cerebral'

export default (allele) => {
    return Compute(allele, (allele, get) => {
        if (!allele) {
            return []
        }

        let warnings = []
        if (allele.warnings) {
            warnings = warnings.concat(
                Object.values(allele.warnings).map((w) => {
                    return { warning: w }
                })
            )
        }
        return warnings
    })
}
