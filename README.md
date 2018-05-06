# CIBERSORT-wrapper

##### A shell to facilitate loading / calling CIBERSORT software in structured environments and through a python module

I am not an author of CIBERSORT nor am I affiliated with thier group.

Find the official CIBERSORT package here:

https://cibersort.stanford.edu/index.php

CIBERSORT is **NOT** freely available for download or distribution, and at the time of creation of this wrapper, the package license does not permit redistribution. You will need to request the code from the CIBERSORT administrators to use this wrapper and adhere to all of thier license restrictions. The Apache 2.0 license here only referse to the CIBERSORT-wrapper code.

And if you find this useful, please cite the authors' publication:

Newman AM, Liu CL, Green MR, Gentles AJ, Feng W, Xu Y, Hoang CD, Diehn M,
Alizadeh AA. Robust enumeration of cell subsets from tissue expression profiles. 
Nat Methods. 2015 May;12(5):453-7. doi: 10.1038/nmeth.3337. Epub 2015 Mar 30.
PubMed PMID: 25822800; PubMed Central PMCID: PMC4739640.

## Installation

### 1. Acquire a licensed distribution of the CIBERSORT source from the CIBERSORT website.

https://cibersort.stanford.edu/index.php This involves a request, a waiting period, email confirmation, and limited time download.  Also be read the license agreement carefully since it contains a lot of clauses that would be hard to find in any academic project.  The most relevant one to this guide is **no distribution**.  This wrapper does **not** include CIBERSORT software nor does it grant any license to distribute CIBERSORT software loaded into a docker.

If the file you get access to is the file with v1.06 in its jar file, it will be a zip file such as

`CIBERSORT_package.zip`


### 2. Clone this repository and into its directory.

```
$ git clone https://github.com/jason-weirather/CIBERSORT.git
$ cd CIBERSORT
```

### 3. Copy CIBERSORT into this wrapper and expand if running locally.

```
$ cp ~/Downloads/CIBERSORT_package.zip ./
````

(method A: Docker) If you are building the docker, you don't have to expand this file.  (if its what this wrapper is expecting).

(method B: Local install) From inside repository directory expand it into CIBERSORT_DISTRIBUTION using the included script.

```
$ sh steps.sh
```

Not this is not a bundled directory so if you unzip it, it will explode into its desitination. The following contents are what this wrapper is expecting.

```
.
├── CIBERSORT.jar
├── CIBERSORT_documentation.txt
├── CIBERSORT_license.txt
├── ExampleMixtures-GEPs.txt
├── ExampleMixtures-GroundTruth.txt
├── FinalMixtureMatrix.Abbas.HCT116.Res30.subset.txt
├── FinalMixtureMatrix.Spike.Abbas.coloncancer.subset.txt
├── GSE11103_matrix_classes.GSE11103_matrix_pure.bm.K999.0.txt
├── GSE11103_matrix_classes.txt
├── GSE11103_matrix_mixtures.txt
├── GSE11103_matrix_pure.txt
├── LM22.txt
└── lib
    ├── CCLE_nonBlood_Avgs.txt
    ├── REngine.jar
    ├── RserveEngine.jar
    ├── XavierGEP.NonImmune.txt
    ├── commons-math-2.2.jar
    └── jsch-0.1.44.jar
```

### 4. Docker Install

From inside the repository directory build the docker:

```
$ docker build . -t cibersort:1.06
```

Now the python wrapper command is available via docker.
```
$ docker run --rm cibersort:1.06 CIBERSORT
usage: CIBERSORT [-h] [--mixture_file MIXTURE_FILE] [--tsv_in] [--tsv_out]
                 [--output OUTPUT] [--absolute ABSOLUTE] [--verbose]
                 [--nperm NPERM]
                 [--tempdir TEMPDIR | --specific_tempdir SPECIFIC_TEMPDIR]
                 input
CIBERSORT: error: the following arguments are required: input
```

If you can also access the original java command is also exposed. Here `CIBERSORT.jar` is just shell script that fires up the Rserver and sets `-Xmx3g -Xms3g` options.  You can put all your options after this command and run it like the java command.
```
$ docker run --rm cibersort:1.06 CIBERSORT.jar
=======================================================
                   CIBERSORT v1.06
    Cell-type Identification By Estimating Relative
               Subsets Of RNA Transcripts

            Newman et al., Nat Methods 2015
                 doi:10.1038/nmeth.3337
=======================================================

>Usage:
R CMD Rserve --no-save
java -jar CIBERSORT.jar -M Mixture -B Signature_Matrix [Options]

>Note:
At least 3 parallel threads required for Unix systems (1 thread for Windows systems)
At least 2GB RAM recommended, e.g. for 3GB:
java -jar -Xmx3g -Xms3g -jar CIBERSORT.jar ...

>Options:
Argument   Description (details or default value)
--------   --------------------------------------
-M File    [Required] Mixture file (GEP matrix: row 1 = sample labels; column 1 = gene symbols; no missing values)
-B File    Signature matrix file (Cell type GEP barcode matrix: row 1 = sample labels; column 1 = gene symbols; no missing values)
           *This argument supersedes -P and -c (below) which collectively are used to build a signature matrix
-P File    Purified sample file (Purified cell GEP matrix: row 1 = sample labels; column 1 = gene symbols; no missing values)
-c File    Phenotype classes (Each row: phenotype label followed by 1 (class of interest), 2 (compare against), or 0 (ignore))
-n Integer Set number of permutations for statistical analysis (100)
-A         Run CIBERSORT in absolute mode (False)
-a         Disable sum-to-1 constraint in absolute mode (signature gene score used by default; see website for details)
-v         Enable verbose output for web version (% complete for permutations and CIBERSORT)
-q [0-1]   Set q-value cutoff for differential expression analysis (0.3)
-k Integer Set maximum condition number, or kappa, for signature matrix (999)
-m Integer Set minimum number of DEGs to consider from each phenotype for signature matrix (50)
-x Integer Set maximum number of DEGs to consider from each phenotype for signature matrix (150)
-g         Merge cell types during signature matrix construction to reduce kappa until below maximum threshold  (False)
-f         Filter non-hematopoietic genes from signature matrix during construction (False)
-S         Remake signature gene matrix (False)
```

### 5. Local Install

#### A. Install the requirements for CIBERSORT (and make sure you have python3 for this wrapper)

Descriptions are in the CIBERSORT documentation.

Conda packages that currently effectively meet these requirements are

```
    - python 3*
    - r 3.4.1*
    - openjdk 8.0.144*
    - r-rserve 1.7_3*
    - r-e1071 1.6_8*
    - r-colorramps 2.3*
    - bioconductor-preprocesscore 1.40.0*
```

You can install these yourself, or I recommend using the conda environment I made for these requirements.

```
$ conda create -n CIBERSORT -c vacation cibersort
$ source activate CIBERSORT
(CIBERSORT) $
```

#### B. Install the CIBERSORT wrapper

From within this repositories directory, and if you are using conda, from within your conda environment do the following:

```
(CIBERSORT) $ pip install -e .
```

Now the CIBERSORT command should be available.

```
(CIBERSORT) $ CIBERSORT
usage: CIBERSORT [-h] [--mixture_file MIXTURE_FILE] [--tsv_in] [--tsv_out]
                 [--output OUTPUT] [--absolute ABSOLUTE] [--verbose]
                 [--nperm NPERM]
                 [--tempdir TEMPDIR | --specific_tempdir SPECIFIC_TEMPDIR]
                 input
CIBERSORT: error: the following arguments are required: input
```

