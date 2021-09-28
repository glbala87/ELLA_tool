from vardb.util.vcfiterator import VcfIterator

vi = VcfIterator("HG002-Trio.Mendeliome_v01.vcf")
with open("HG002-Trio.Mendeliome_v01.sliced.raw.filtered.vcf", "w") as out:
    for line, data in vi.iter(include_raw=True):
        if all(data["SAMPLES"][k]["GT"] in ["0/1", "1/1", "0/0"] for k in data["SAMPLES"]):
            if "GNOMAD_GENOMES__AF" in data["INFO"]["ALL"]:
                if data["INFO"]["ALL"]["GNOMAD_GENOMES__AF"][0] > 0.2:
                    print("Filtered")
                    continue
        out.write(line + "\n")
