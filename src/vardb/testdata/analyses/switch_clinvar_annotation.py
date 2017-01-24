import os
import re
import gzip
import numpy as np

# Find all vcf files
def vcf_files():
    for f in os.walk('.'):
        if f[0] == ".":
            continue
        for filename in f[2]:
            if filename.endswith(".vcf"):
                if os.path.islink(os.path.join(f[0], filename)):
                    continue
                yield os.path.join(f[0], filename)

def exclude_info_pattern(vcf_file, pattern):
    newlines = []
    with open(vcf_file, 'r') as f:
        lines = f.readlines()
    
    #it = reversed(lines)
    it = iter(lines)

    for l in it:
        if l.startswith("#CHROM"):
            newlines.append(l)
            break
        if re.search("##INFO=<ID="+pattern, l) is None:
            newlines.append(l)

    for l in it:
        cols = l.split("\t")
        #print cols
        cols[7] = re.sub(pattern+"?;", "", cols[7])
        newlines.append("\t".join(cols))

    with open(vcf_file, 'w') as f:
        f.write("".join(newlines))

def run_vcfanno(vcf_file):
    with open("config.toml", 'w') as f:
        f.write('[[annotation]]\n')
        f.write('file="clinvar_refined.vcf.gz"\n')
        f.write('fields=["CLINVARJSON"]\n')
        f.write('names=["CLINVARJSON"]\n')
        f.write('ops=["self"]\n')
    
    #with
    def fix_fileformat(vcf_file):
        with open(vcf_file, 'r') as f:
            first = f.readline()
            if first.startswith("##fileformat"):
                return
            data = first+f.read()
        
        with open(vcf_file, 'w') as f:
            f.write("##fileformat=VCFv4.1\n"+data)

    def sort(vcf_file, idx=None, argsort=False):
        f = open("tmp", 'w')
        vcf = open(vcf_file, 'r')
        it = iter(vcf)
        for l in it:
            f.write(l)
            if "#CHROM" in l:
                break
        lines = [l for l in it]
        if idx is None:
            def convert(x):
                try:
                    X = int(x)
                except:
                    X = 24
                return X

            arr = np.array([[convert(l.split('\t')[0]), convert(l.split('\t')[1])] for l in lines])
            idx = np.lexsort((arr[:, 0], arr[:, 1]))
            if argsort:
                return idx
        for i in idx:
            f.write(lines[i])
        f.close()
        vcf.close()
        os.system("mv tmp "+vcf_file)
        return idx

    def unsort(vcf_file, idx):
        return sort(vcf_file, idx)


    #fileformat=VCFv4.1\n
    fix_fileformat(vcf_file)
    #err = os.system("cat %s | vcf-sort > tmp" %(vcf_file))
    #assert err == 0
    idx = sort(vcf_file)

    err = os.system("vcfanno config.toml "+vcf_file +"> tmp")  
    assert err == 0
    
    with open("tmp") as f:
        data = f.readlines()
        for i, l in enumerate(data):
            if "##INFO=<ID=CLINVARJSON" in l:
                break

    ref = gzip.open("clinvar_refined.vcf.gz",'r')
    for l in ref:
        if "##INFO=<ID=CLINVARJSON" in l:
            break
    data[i] = l
    
    with open(vcf_file, 'w') as f:
        f.write("".join(data))

    idx = list(idx)
    unsort(vcf_file, [idx.index(i) for i in range(len(idx))])
    idx2 = sort(vcf_file, argsort=True)
    assert all(idx==idx2)

if __name__ == '__main__':
    
    # For each vcf file:
    for f in vcf_files():
        print f
        exclude_info_pattern(f, "CLINVAR.*")
        run_vcfanno(f)
        print f
        err = os.system("vcf-validator %s" %f)
        assert err == 0
        #exit()
        #rewrite_description()