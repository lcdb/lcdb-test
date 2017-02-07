import pytest
import pysam
from snakemake.shell import shell
from lcdblib.snakemake import aligners
from utils import run, dpath, rm, symlink_in_tempdir


def test_hisat2_build(dm6_fa, tmpdir):
    snakefile = '''
                rule hisat2_build:
                    input:
                        fasta='2L.fa'
                    output:
                        index=expand('data/assembly/assembly.{n}.ht2', n=range(1,9))
                    log: 'hisat.log'
                    wrapper: "file:wrapper"

                '''
    input_data_func=symlink_in_tempdir(
        {
            dm6_fa: '2L.fa'
        }
    )

    def check():
        assert 'Total time for call to driver' in open('hisat.log').readlines()[-1]
        assert list(shell('hisat2-inspect data/assembly/assembly -n', iterable=True)) == ['2L']

    run(dpath('../wrappers/hisat2/build'), snakefile, check, input_data_func, tmpdir)


def _dict_of_hisat2_indexes(hisat2_indexes, prefix):
    d = {}
    indexes = aligners.hisat2_index_from_prefix(prefix)
    hisat2_indexes = sorted(hisat2_indexes)
    indexes = sorted(indexes)
    for k, v in zip(hisat2_indexes, indexes):
        d[k] = v
    return d


def test_hisat2_align_se(hisat2_indexes, sample1_se_fq, tmpdir):
    d = _dict_of_hisat2_indexes(hisat2_indexes, '2L')
    indexes = list(d.values())
    snakefile = '''
        rule hisat2_align:
            input:
                fastq='sample1_R1.fastq.gz',
                index={indexes}
            output:
                bam='sample1.bam'
            log: "hisat2.log"
            wrapper: "file:wrapper"
    '''.format(indexes=indexes)
    d[sample1_se_fq] = 'sample1_R1.fastq.gz'
    input_data_func = symlink_in_tempdir(d)

    def check():
        assert "overall alignment rate" in open('hisat2.log').read()

        # should have at least some mapped and unmapped
        assert int(list(shell('samtools view -c -f 0x04 sample1.bam', iterable=True))[0]) > 0
        assert int(list(shell('samtools view -c -F 0x04 sample1.bam', iterable=True))[0]) > 0

    run(dpath('../wrappers/hisat2/align'), snakefile, check, input_data_func, tmpdir)


def test_hisat2_align_se_SRA(hisat2_indexes, tmpdir):
    d = _dict_of_hisat2_indexes(hisat2_indexes, '2L')
    indexes = list(d.values())
    snakefile = '''
        rule hisat2_align:
            input:
                index={indexes}
            output:
                bam='sample1.bam'
            params: hisat2_extra='--sra-acc SRR1990338'
            log: "hisat2.log"
            wrapper: "file:wrapper"
    '''.format(indexes=indexes)
    input_data_func = symlink_in_tempdir(d)

    def check():
        assert "overall alignment rate" in open('hisat2.log').read()

        # should have at least some mapped and unmapped
        assert int(list(shell('samtools view -c -f 0x04 sample1.bam', iterable=True))[0]) > 0
        assert int(list(shell('samtools view -c -F 0x04 sample1.bam', iterable=True))[0]) > 0

    run(dpath('../wrappers/hisat2/align'), snakefile, check, input_data_func, tmpdir)


def test_hisat2_align_se_rm_unmapped(hisat2_indexes, sample1_se_fq, tmpdir):
    d = _dict_of_hisat2_indexes(hisat2_indexes, '2L')
    indexes = list(d.values())
    snakefile = '''
        rule hisat2_align:
            input:
                fastq='sample1_R1.fastq.gz',
                index={indexes}
            output:
                bam='sample1.bam'
            params:
                samtools_view_extra='-F 0x04'
            log: "hisat2.log"
            wrapper: "file:wrapper"
    '''.format(indexes=indexes)
    d[sample1_se_fq] = 'sample1_R1.fastq.gz'
    input_data_func = symlink_in_tempdir(d)

    def check():
        assert "overall alignment rate" in open('hisat2.log').read()

        # should have at least some mapped and unmapped
        assert int(list(shell('samtools view -c -f 0x04 sample1.bam', iterable=True))[0]) == 0
        assert int(list(shell('samtools view -c -F 0x04 sample1.bam', iterable=True))[0]) > 0

    run(dpath('../wrappers/hisat2/align'), snakefile, check, input_data_func, tmpdir)
