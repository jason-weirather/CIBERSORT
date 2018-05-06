"""Execute CIBERSORT transformation of gene expression.

This python package gives both a CLI interface and a python module to work with CIBERSORT in Python Pandas DataFrames.

I am not an author of CIBERSORT nor am I affiliated with thier group.

Find the official CIBERSORT package here:

https://cibersort.stanford.edu/index.php

CIBERSORT is **NOT** freely available for download or distribution, and at the time of creation of this wrapper, the package license does not permit redistribution. You will need to request the code from the CIBERSORT administrators to use this wrapper and adhere to all of thier license restrictions. The Apache 2.0 license here only referse to the CIBERSORT-wrapper code.

And if you find this useful, please cite the authors' publication:

Newman AM, Liu CL, Green MR, Gentles AJ, Feng W, Xu Y, Hoang CD, Diehn M,
Alizadeh AA. Robust enumeration of cell subsets from tissue expression profiles. 
Nat Methods. 2015 May;12(5):453-7. doi: 10.1038/nmeth.3337. Epub 2015 Mar 30.
PubMed PMID: 25822800; PubMed Central PMCID: PMC4739640.

"""
import argparse, sys, os, re
import pandas as pd 
from tempfile import mkdtemp, gettempdir
from subprocess import Popen, PIPE, call

__cur = os.path.dirname(os.path.realpath(__file__))
__sourcedir = os.path.realpath(os.path.join(__cur,'../CIBERSORT_DISTRIUBTION/'))
LM22 = pd.read_csv(os.path.join(__sourcedir,'LM22.txt'),sep="\t").set_index('Gene symbol').applymap(float)


def CIBERSORT(expression_df,
              absolute=True,
              nperm=500,
              mixture_file=None,
              verbose=False,
              tempdir= None):
    """CIBERSORT function for use with pandas DataFrame objects

    :param expression_df: REQUIRED: Expression data indexed on gene names column labels as sample ids
    :type expression_df: pandas.DataFrame
    :param absolute: Run CIBERSORT in absolute mode Default: True
    :type absolute: Bool
    :param mixture_file: Mixture file. Default: LM22
    :type mixture_file: pandas.DataFrame
    :param verbose: Gives information about each calculation step.
    :type verbose: bool Default: False
    :param tempdir: Location to write temporary files
    :type tempdir: string Default: System Default
    :returns: pandas.DataFrame
    """
    expression_df
    if mixture_file is None: mixture_file = LM22
    if not tempdir:
        tempdir =  mkdtemp(prefix="weirathe.",dir=gettempdir().rstrip('/'))
    else:
        if not os.path.exists(tempdir):
            os.makedirs(tempdir)
    if verbose:
        sys.stderr.write("Caching to "+tempdir+"\n")

    cmd1 = ["Rscript","-e","library(Rserve);Rserve(args=\"--no-save\")"]
    expression_df.to_csv(os.path.join(tempdir,"expr.tsv"),sep="\t")
    mixture_file.to_csv(os.path.join(tempdir,"mixture.tsv"),sep="\t")
    if verbose: sys.stderr.write(__sourcedir+"\n")
    cmd2 = ["java","-Xmx3g","-Xms3g","-jar",os.path.join(__sourcedir,"CIBERSORT.jar"),"-n",str(nperm),"-M",os.path.join(tempdir,"expr.tsv"),"-B",os.path.join(tempdir,"mixture.tsv")]
    if absolute: cmd2 += ["-A"]
    if verbose: sys.stderr.write(" ".join(cmd1)+"\n")
    FNULL = open(os.devnull, 'w')
    call(cmd1,stdout=FNULL,stderr=FNULL)
    if verbose: sys.stderr.write(" ".join(cmd2)+"\n")
    sp = Popen(cmd2,stdout=PIPE,stderr=PIPE).communicate()
    if verbose:
        for line in sp[1]: sys.stderr.write(line.decode('utf-8'))
    if verbose: sys.stderr.write("finished R script\n")
    output = []
    lines = [x for x in sp[0].decode('utf-8').rstrip().split('\n')]
    passed_header = False
    for i, line in enumerate(lines.copy()):
        if passed_header: output.append(line.split("\t"))
        if re.match('>====+CIBERSORT===',line):
            passed_header = True
    df = pd.DataFrame(output[1:],columns=[x for x in output[0] if x != '']).set_index('Column')
    df.index = expression_df.columns
    #df.index.name = 'Sample'
    #df = df.reset_index()
    #if not absolute:
    #    df.set_index(['Sample','P-value','Pearson Correlation','RMSE'])
    #else:
    #    df.set_index(['Sample','P-value','Pearson Correlation','Absolute score'])
    df = df.applymap(float)
    return df


def __cli():
    args = __do_inputs()
    # Now read in the input files for purposes of standardizing inputs
    df = None
    if args.tsv_in:
        df = pd.read_csv(args.input,sep="\t",index_col=0)
    else:
        df = pd.read_csv(args.input,index_col=0)
    if not args.mixture_file: mixture_file = None
    elif args.tsv_in: mixture_file = pd.read_csv(mixture_file,sep="\t",index_col=0)
    else: mixture_file = pd.read_csv(mixture_file,index_col=0)
    result = CIBERSORT(df,
                  absolute=args.absolute,
                  nperm=args.nperm,
                  mixture_file=mixture_file,
                  verbose=args.verbose,
                  tempdir= args.tempdir
                 )
    sep = ','
    if args.tsv_out: sep = "\t"
    if args.output:
        result.to_csv(args.output,sep=sep)
    else:
        result.to_csv(os.path.join(args.tempdir,'final.csv'),sep=sep)
        with open(os.path.join(args.tempdir,'final.csv')) as inf:
            for line in inf:
                sys.stdout.write(line)

def __do_inputs():
    # Setup command line inputs
    parser=argparse.ArgumentParser(description="Execute CIBERSORT",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    group0 = parser.add_argument_group('Input options')
    group0.add_argument('input',help="Use - for STDIN")
    group0.add_argument('--mixture_file',help="Set a mixture file path")
    group0.add_argument('--tsv_in',action='store_true',help="Exepct CSV by default, this overrides to tab")


    group2 = parser.add_argument_group('Output options')
    group2.add_argument('--tsv_out',action='store_true',help="Override the default CSV and output TSV")
    group2.add_argument('--output','-o',help="Specifiy path to write transformed data")


    group1 = parser.add_argument_group('command options')
    absolute_str = '''
Execute in absolute mode.
    '''
    group1.add_argument('--absolute',type=bool,default=True,help=absolute_str)
    verbose_str = '''
Gives information about each calculation step.
    '''
    group1.add_argument('--verbose',action='store_true',help=verbose_str)
    nperm_str = '''
Number of random resamplings.
    '''
    group1.add_argument('--nperm',type=int, default=500,help=nperm_str)

    # Temporary working directory step 1 of 3 - Definition
    label4 = parser.add_argument_group(title="Temporary folder parameters")
    group3 = label4.add_mutually_exclusive_group()
    group3.add_argument('--tempdir',default=gettempdir(),help="The temporary directory is made and destroyed here.")
    group3.add_argument('--specific_tempdir',help="This temporary directory will be used, but will remain after executing.")


    args = parser.parse_args()
    setup_tempdir(args)
    return args  

def setup_tempdir(args):
  if args.specific_tempdir:
    if not os.path.exists(args.specific_tempdir):
      os.makedirs(args.specific_tempdir.rstrip('/'))
    args.tempdir = args.specific_tempdir.rstrip('/')
    if not os.path.exists(args.specific_tempdir.rstrip('/')):
      sys.stderr.write("ERROR: Problem creating temporary directory\n")
      sys.exit()
  else:
    args.tempdir = mkdtemp(prefix="weirathe.",dir=args.tempdir.rstrip('/'))
    if not os.path.exists(args.tempdir.rstrip('/')):
      sys.stderr.write("ERROR: Problem creating temporary directory\n")
      sys.exit()
  if not os.path.exists(args.tempdir):
    sys.stderr.write("ERROR: Problem creating temporary directory\n")
    sys.exit()
  return

if __name__=="__main__":
  __cli()

