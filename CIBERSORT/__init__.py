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
GENCODE = pd.read_csv(os.path.realpath(os.path.join(__sourcedir,'../data/gencode_conversions.csv')))
__valid_types = sorted(GENCODE['library'].unique())
GENCODEIDS = pd.read_csv(os.path.realpath(os.path.join(__sourcedir,'../data/gencode_id_to_name.csv')))

def CIBERSORT(expression_df,
              absolute=True,
              nperm=100,
              mixture_file=None,
              input_type = None,
              gencode_id_format = False,
              verbose=False,
              tempdir= None):
    """CIBERSORT function for use with pandas DataFrame objects

    :param expression_df: REQUIRED: Expression data indexed on gene names column labels as sample ids
    :type expression_df: pandas.DataFrame
    :param absolute: Run CIBERSORT in absolute mode Default: True
    :type absolute: Bool
    :param mixture_file: Mixture file. Default: LM22
    :type mixture_file: pandas.DataFrame
    :param input_type: Is this a gencode reference. Default: None
    :type input_type: string
    :param gencode_id_format: Input is gencode ids. Default: False
    :type gencode_id_format: bool
    :param verbose: Gives information about each calculation step.
    :type verbose: bool Default: False
    :param tempdir: Location to write temporary files
    :type tempdir: string Default: System Default
    :returns: pandas.DataFrame
    """
    if input_type:
        if gencode_id_format == True and not input_type: raise ValueError("if these are gencode ids you must specify a valid input_type "+str(__valid_types))
        if input_type not in __valid_types:
            raise ValueError("trying to cross a library type that hasn't been defined as "+str(__valid_types))
        if gencode_id_format:
            sub = GENCODEIDS[GENCODEIDS['library']==input_type]
            conv = dict(zip(list(sub['gene_id']),list(sub['gene_name'])))
            expression_df = expression_df.rename(index=conv)
            expression_df.index.name = 'gene_name'
            expression_df = expression_df.reset_index().groupby('gene_name').first()

        rows = GENCODE[GENCODE['library']==input_type]
        v = GENCODE[GENCODE['library']==input_type]
        conv = dict(zip(
            list(v['gencode']),
            list(v['CIBERSORT'])
        ))
        expression_df = expression_df.rename(index=conv)
        expression_df.index.name = 'gene_name'
        expression_df = expression_df.reset_index().groupby('gene_name').first()

    if mixture_file is None: mixture_file = LM22
    if not tempdir:
        tempdir =  mkdtemp(prefix="weirathe.",dir=gettempdir().rstrip('/'))
    else:
        if not os.path.exists(tempdir):
            os.makedirs(tempdir)
    if verbose:
        sys.stderr.write("Caching to "+tempdir+"\n")

    cmd1 = ["Rscript","-e","library(Rserve);Rserve(args=\"--no-save\")"]
    if verbose:
        sys.stderr.write("Evaluating based on "+str(expression_df.index.intersection(mixture_file.index).shape[0])+'/'+str(mixture_file.index.shape[0])+" signature genes\n")
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
    df = df.applymap(float).T
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
                  input_type=args.input_type,
                  gencode_id_format=args.gencode_id_foramt,
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
    group1.add_argument('--nperm',type=int, default=100,help=nperm_str)
    input_type_str = '''
If there was a gencode source.
    '''
    group1.add_argument('--input_type',choices=__valid_types,help=input_type_str)
    gencode_id_format_str = '''
If set indicates this dataset is in gencode gene_id format labels.
    '''
    group1.add_argument('--gencode_id_format',action='store_true',help=gencode_id_format_str)

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

