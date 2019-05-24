**BuildingOpt_OT.py**: Runs multiopjective optimization on the small office building for the problem declared in SOProblems_OT.py

**EPDataModule.py**: Loads the energy plus simulation data that will be used for the uncertainty analysis.

**GenerateEnergyPlusData.py**: This script will generate energy plus model data with different sample sizes to use in UA and SA.

**GenerateMetaModel.py**: Script used to generate meta model for energy plus building simulations for each of the desired outputs.
This script will read a json input file for a set of energy plus building model inputs and parameters and run a
simulation for each set of input parameters. After obtaining the energy usage and thermal comfort outputs for each
parameter set, it will fit a regression model.

**GenerateTrainingDataFEEOpt**: This script will take in an idf file as an input and will generate a .txt file containing the idf parameters and
relevant information for identifying the parameters associated with FEE Opt 10 and 5 in the building model in json format.

**GenerateTrainingDataPMVOpt**: This script will take in an idf file as an input and will generate a .txt file containing the idf parameters and
relevant information for identifying the parameters associated with PMV Opt 10 and 5 in the building model in json format.

**GenerateTrainingData**: This script will take in an idf file as an input and will generate a .txt file containing the idf parameters and
relevant information for identifying the parameters associated with the three groups of parameters looked at in the UA.

**MetaModelConvergence.py**: This script will compare the output distributions for the energy plus model simulations and the gaussian process
regression fit for the same data sets for a range of sample sets. In order to compare the distributions, a
bhattacharyya distance is calculated for each model that was calculated with a different sample set size. The
objective here is to find the sufficient sample size that allows the gaussian process model and the energy plus model
distrubutions to match.

**SOProblems_OT.py**: This will define an optimization problem based on the small office EnergyPlus model.

**SensitivityCalculation**: This script will use the gaussian process regression models generated for the energy plus simulations in order to
pwerform a sensitivity analysis on all of the input parameters by calculating DGSM indices.

**SmallOfficeModules**: Configures the small office idf file in order to set up the correct outputs and simulation run parameters.
