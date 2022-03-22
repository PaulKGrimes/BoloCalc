#########################
####### BoloCalc ########
#########################

BoloCalc is a sensitivity calculator for cosmic microwave background (CMB) instruments.

A user manual, which includes a "Quick Start Guide," can be found in the MANUAL/ directory.

This version of the code has been updated by Paul Grimes to include Sphinx auto-generated documentation of the Python code.

Please cite https://arxiv.org/abs/1806.04316 if you use this code to generate NETs for publication.

#########################
### Quick Start Guide ###
#########################

* To install the needed packages and download atmosphere data, run
    $ python init.py

* To download experiment data, run
    $ cd Experiments/
    $ python importExperiments.py
and follow the command-line-argument instructions. An "example experiment" is provided by default,
but other available experiment data is password protected. Check the user manual for information
about how to access protected data.

* To simulate the example experiment, run
    $ python calcBolos.py Experiments/ExampleExperiment/V0/
The outputs are generated in "sensitivity.txt" files within "ExampleExperiment/V0/" directory.
