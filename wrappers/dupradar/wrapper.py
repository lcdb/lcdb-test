import tempfile
from snakemake.shell import shell
from lcdblib.snakemake import helpers

extra = snakemake.params.get('extra', '')
log = snakemake.log_fmt_shell()

stranded = snakemake.params.get('stranded', False)
try:
    stranded_int = {False: 0, True: 1, 'reverse': 2}[stranded]
except KeyError:
    raise ValueError('"stranded" must be True|False|"reverse"')

paired = snakemake.params.get('paired', False)
try:
    paired_bool= {True: 'TRUE', False: 'FALSE'}[paired]
except KeyError:
    raise ValueError('"paired" must be True or False')

# To avoid issues with png() related to X11 and cairo, we can use bitmap() instead.
# (thanks
# http://stackoverflow.com/questions/24999983/
# r-unable-to-start-device-png-capabilities-has-true-for-png
# #comment52353278_25064603 )

script = """
library(dupRadar)
bam <- "{snakemake.input.bam}"
gtf <- "{snakemake.input.annotation}"
dm <- analyzeDuprates(bam, gtf, {stranded_int}, {paired_bool}, {snakemake.threads})

dm$mhRate <- (dm$allCountsMulti - dm$allCounts) / dm$allCountsMulti
bitmap(file="{snakemake.output.multimapping_histogram}")
hist(dm$mhRate, breaks=50, main=basename(bam),
    xlab="Multimapping rate per gene", ylab="Frequency")
dev.off()

bitmap(file="{snakemake.output.density_scatter}")
duprateExpDensPlot(dm, main=basename(bam))
dev.off()

bitmap(file="{snakemake.output.expression_histogram}")
expressionHist(dm)
dev.off()

bitmap(file="{snakemake.output.expression_boxplot}")
par(mar=c(10,4,4,2)+.1)
duprateExpBoxplot(dm, main=basename(bam))
dev.off()

bitmap(file="{snakemake.output.expression_barplot}")
readcountExpBoxplot(dm)
dev.off()

write.table(dm, file="{snakemake.output.dataframe}", sep="\\t")
""".format(**locals())

tmp = tempfile.NamedTemporaryFile(delete=False).name
helpers.rscript(script, tmp, log=log)
