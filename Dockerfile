# CIBERSORT wrapper Python module and CLI
# This is a wraper of CIBERSORT for CLI and python module use. 
# It does not contain the CIBERSORT software.
#    for the CIBERSORT distribution see
#    https://cibersort.stanford.edu/index.php
# If used cite: 
#    Newman AM, Liu CL, Green MR, Gentles AJ, Feng W, Xu Y, Hoang CD, Diehn M,
#    Alizadeh AA. Robust enumeration of cell subsets from tissue expression profiles. 
#    Nat Methods. 2015 May;12(5):453-7. doi: 10.1038/nmeth.3337. Epub 2015 Mar 30.
#    PubMed PMID: 25822800; PubMed Central PMCID: PMC4739640.
FROM continuumio/anaconda:5.1.0
ENV HOME /root
RUN apt-get update && apt-get install -y unzip

ADD . /opt/CIBERSORT

RUN cd /opt/CIBERSORT/ && bash steps.sh

RUN cp /opt/CIBERSORT/.condarc /root/.condarc
RUN conda create -n CIBERSORT -c vacation cibersort=1.01
RUN echo 'source activate CIBERSORT' >> /root/.bashrc
RUN cd /opt/CIBERSORT/ && /opt/conda/envs/CIBERSORT/bin/pip install -e .

WORKDIR /root
ENTRYPOINT ["/opt/CIBERSORT/exec.sh"]
