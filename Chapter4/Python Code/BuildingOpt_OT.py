############################################################
# Kaden Plewe
# 3/5/2019
# Optimization Model for SEB Single Thermal Zone Building
############################################################

# import libraries
#################################################
from SOProblems_OT import SO1, SO2
from platypus import *
import matplotlib.pyplot as plt
import json
import numpy as np
import random
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import seaborn as sns

'''run the optimization for the specific data set'''

'''define the problem that is being solved'''
# problem = SO('7', '17', '7', '19')

'''instantiate the optimization algorithm'''
# algorithm = NSGAII(problem)
# algorithm = NSGAIII(problem, divisions_outer=6)
# algorithm = CMAES(problem, epsilons=[0.05])
##algorithm = GDE3(problem)
# algorithm = IBEA(problem)
# algorithm = MOEAD(problem, weight_generator=normal_boundary_weights, divisions_outer=12)
# algorithm = OMOPSO(problem, epsilons=[0.05])
# algorithm = SMPSO(problem)
# algorithm = SPEA2(problem)
# algorithm = EpsMOEA(problem, epsilons=[0.05])

'''optimize the problem using 10,000 function evaluaions'''
# input('press a key to start algorithm run \n')
# algorithm.run(100)
#
# for solution in algorithm.result:
#     print(solution.variables)
#
'''save/load variables and objectives'''
# np.save(optResultName, algorithm.result)
# np.save(optVarName, solution.variables)
# np.save(optObjName, solution.objectives)


'''load results that will be compared for sensitivity analysis'''
Baseline_fn1 = np.load('Baseline_results1.npy')
Baseline_fn2 = np.load('Baseline_results2.npy')
Baseline_fn3 = np.load('Baseline_results3.npy')
Baseline_fn4 = np.load('Baseline_results4.npy')
PMVOpt5_fn1 = np.load('PMVOpt5_results1.npy')
PMVOpt5_fn2 = np.load('PMVOpt5_results2.npy')
PMVOpt5_fn3 = np.load('PMVOpt5_results3.npy')
PMVOpt5_fn4 = np.load('PMVOpt5_results4.npy')
PMVOpt10_fn1 = np.load('PMVOpt10_results1.npy')
PMVOpt10_fn2 = np.load('PMVOpt10_results2.npy')
PMVOpt10_fn3 = np.load('PMVOpt10_results3.npy')
PMVOpt10_fn4 = np.load('PMVOpt10_results4.npy')
FEEOpt5_fn1 = np.load('FEEOpt5_results1.npy')
FEEOpt5_fn2 = np.load('FEEOpt5_results2.npy')
FEEOpt5_fn3 = np.load('FEEOpt5_results3.npy')
FEEOpt5_fn4 = np.load('FEEOpt5_results4.npy')
FEEOpt10_fn1 = np.load('FEEOpt10_results1.npy')
FEEOpt10_fn2 = np.load('FEEOpt10_results2.npy')
FEEOpt10_fn3 = np.load('FEEOpt10_results3.npy')
FEEOpt10_fn4 = np.load('FEEOpt10_results4.npy')

'''objective points'''
Baseline_ip1 = [(s.objectives[0], s.objectives[1]) for s in Baseline_fn1]
Baseline_ip2 = [(s.objectives[0], s.objectives[1]) for s in Baseline_fn2]
Baseline_ip3 = [(s.objectives[0], s.objectives[1]) for s in Baseline_fn3]
Baseline_ip4 = [(s.objectives[0], s.objectives[1]) for s in Baseline_fn4]
PMVOpt5_ip1 = [(s.objectives[0], s.objectives[1]) for s in PMVOpt5_fn1]
PMVOpt5_ip2 = [(s.objectives[0], s.objectives[1]) for s in PMVOpt5_fn2]
PMVOpt5_ip3 = [(s.objectives[0], s.objectives[1]) for s in PMVOpt5_fn3]
PMVOpt5_ip4 = [(s.objectives[0], s.objectives[1]) for s in PMVOpt5_fn4]
PMVOpt10_ip1 = [(s.objectives[0], s.objectives[1]) for s in PMVOpt10_fn1]
PMVOpt10_ip2 = [(s.objectives[0], s.objectives[1]) for s in PMVOpt10_fn2]
PMVOpt10_ip3 = [(s.objectives[0], s.objectives[1]) for s in PMVOpt10_fn3]
PMVOpt10_ip4 = [(s.objectives[0], s.objectives[1]) for s in PMVOpt10_fn4]
FEEOpt5_ip1 = [(s.objectives[0], s.objectives[1]) for s in FEEOpt5_fn1]
FEEOpt5_ip2 = [(s.objectives[0], s.objectives[1]) for s in FEEOpt5_fn2]
FEEOpt5_ip3 = [(s.objectives[0], s.objectives[1]) for s in FEEOpt5_fn3]
FEEOpt5_ip4 = [(s.objectives[0], s.objectives[1]) for s in FEEOpt5_fn4]
FEEOpt10_ip1 = [(s.objectives[0], s.objectives[1]) for s in FEEOpt10_fn1]
FEEOpt10_ip2 = [(s.objectives[0], s.objectives[1]) for s in FEEOpt10_fn2]
FEEOpt10_ip3 = [(s.objectives[0], s.objectives[1]) for s in FEEOpt10_fn3]
FEEOpt10_ip4 = [(s.objectives[0], s.objectives[1]) for s in FEEOpt10_fn4]

'''functions used to extract pareto front'''
def simple_cull(inputPoints, dominates):
    paretoPoints = set()
    candidateRowNr = 0
    dominatedPoints = set()
    while True:
        candidateRow = inputPoints[candidateRowNr]
        inputPoints.remove(candidateRow)
        rowNr = 0
        nonDominated = True
        while len(inputPoints) != 0 and rowNr < len(inputPoints):
            row = inputPoints[rowNr]
            if dominates(candidateRow, row):
                # If it is worse on all features remove the row from the array
                inputPoints.remove(row)
                dominatedPoints.add(tuple(row))
            elif dominates(row, candidateRow):
                nonDominated = False
                dominatedPoints.add(tuple(candidateRow))
                rowNr += 1
            else:
                rowNr += 1

        if nonDominated:
            # add the non-dominated point to the Pareto frontier
            paretoPoints.add(tuple(candidateRow))

        if len(inputPoints) == 0:
            break

    return np.array(sorted(paretoPoints, key=lambda pp: pp[0])), np.array(sorted(dominatedPoints, key=lambda dp: dp[0]))

def dominates(row, candidateRow):
    return sum([row[x] <= candidateRow[x] for x in range(len(row))]) == len(row)

'''extract pareto front for all data sets'''
Baseline_pp1, Baseline_dp1 = simple_cull(Baseline_ip1, dominates)
Baseline_pp2, Baseline_dp2 = simple_cull(Baseline_ip2, dominates)
Baseline_pp3, Baseline_dp3 = simple_cull(Baseline_ip3, dominates)
Baseline_pp4, Baseline_dp4 = simple_cull(Baseline_ip4, dominates)
PMVOpt5_pp1, PMVOpt5_dp1 = simple_cull(PMVOpt5_ip1, dominates)
PMVOpt5_pp2, PMVOpt5_dp2 = simple_cull(PMVOpt5_ip2, dominates)
PMVOpt5_pp3, PMVOpt5_dp3 = simple_cull(PMVOpt5_ip3, dominates)
PMVOpt5_pp4, PMVOpt5_dp4 = simple_cull(PMVOpt5_ip4, dominates)
PMVOpt10_pp1, PMVOpt10_dp1 = simple_cull(PMVOpt10_ip1, dominates)
PMVOpt10_pp2, PMVOpt10_dp2 = simple_cull(PMVOpt10_ip2, dominates)
PMVOpt10_pp3, PMVOpt10_dp3 = simple_cull(PMVOpt10_ip3, dominates)
PMVOpt10_pp4, PMVOpt10_dp4 = simple_cull(PMVOpt10_ip4, dominates)
FEEOpt5_pp1, FEEOpt5_dp1 = simple_cull(FEEOpt5_ip1, dominates)
FEEOpt5_pp2, FEEOpt5_dp2 = simple_cull(FEEOpt5_ip2, dominates)
FEEOpt5_pp3, FEEOpt5_dp3 = simple_cull(FEEOpt5_ip3, dominates)
FEEOpt5_pp4, FEEOpt5_dp4 = simple_cull(FEEOpt5_ip4, dominates)
FEEOpt10_pp1, FEEOpt10_dp1 = simple_cull(FEEOpt10_ip1, dominates)
FEEOpt10_pp2, FEEOpt10_dp2 = simple_cull(FEEOpt10_ip2, dominates)
FEEOpt10_pp3, FEEOpt10_dp3 = simple_cull(FEEOpt10_ip3, dominates)
FEEOpt10_pp4, FEEOpt10_dp4 = simple_cull(FEEOpt10_ip4, dominates)




'''plotting initialization'''
'''colors palette and settings used for all ploting'''
from matplotlib.gridspec import GridSpec
# print(plt.rcParams.keys())
plt.style.use('seaborn-deep')
setcolors = sns.hls_palette(10, l=.55, s=.6)
hotcoldcolors = sns.diverging_palette(10, 220, sep=80, n=7)
zonecolors = flatui = ["#95a5a6", "#9b59b6", "#3498db", "chocolate", "#2ecc71", "#34495e"]
externality_colors = ["#be0119", "#7a6a4f", "#94ac02", "#0e87cc", "#887191"]
uncertainty_colors = sns.diverging_palette(220, 20, n=7)
plt.rcParams['font.serif'] = 'DejaVu Serif'
plt.rcParams['figure.figsize'] = 8, 7
plt.rcParams['figure.constrained_layout.use'] = True
plt.rcParams['figure.titlesize'] = 20
plt.rcParams['figure.titleweight'] = 'heavy'
plt.rcParams['axes.titlepad'] = 20
plt.rcParams['axes.labelpad'] = 20
plt.rcParams['legend.loc'] = 'upper left'
plt.rcParams['legend.fontsize'] = 14

axfont = {'family': 'serif',
        'color':  'black',
        'weight': 'normal',
        'size': 16,
        }
axfontsm = {'family': 'serif',
        'color':  'black',
        'weight': 'normal',
        'size': 12,
        }
legendfont = {'family': 'serif',
        'weight': 'light',
        'size': 14,
        }
legendfontsm = {'family': 'serif',
        'weight': 'light',
        'size': 12,
        }
titlefont = {'family': 'serif',
        'color':  'black',
        'weight': 'heavy',
        'size': 20,
        }
titlefontsm = {'family': 'serif',
        'color':  'black',
        'weight': 'heavy',
        'size': 12,
        }
tickfont = {'family': 'serif',
        'color':  'black',
        'weight': 'normal',
        'size': 12,
        }


'''plot pareto fronts for four different samples results'''
figurename = 'paretoresultscomp.jpg'

fig1 = plt.figure(constrained_layout=True, figsize=[10, 7])
# fig2, ax1 = plt.subplots(nrows=1, ncols=1, sharex='col', sharey='row', figsize=[8, 6])
plt.rcParams['axes.titlepad'] = 10
plt.rcParams['axes.labelpad'] = 10

gs = GridSpec(32, 2, figure=fig1)
ax1 = fig1.add_subplot(gs[2:17, 0:1])
ax2 = fig1.add_subplot(gs[2:17, 1:2])
ax3 = fig1.add_subplot(gs[17:32, 0:1])
ax4 = fig1.add_subplot(gs[17:32, 1:2])

'''Trial 1 for all uncertainty sets'''
ax1.plot(Baseline_pp1[:, 0], Baseline_pp1[:, 1], color='k', marker='.', label='Baseline', linewidth=1)
ax1.plot(PMVOpt5_pp1[:, 0], PMVOpt5_pp1[:, 1], color=uncertainty_colors[2], marker='+', label='PMV Opt 5', linewidth=1)
ax1.plot(PMVOpt10_pp1[:, 0], PMVOpt10_pp1[:, 1], color=uncertainty_colors[0], marker='x', label='PMV Opt 10', linewidth=1)
ax1.plot(FEEOpt5_pp1[:, 0], FEEOpt5_pp1[:, 1], color=uncertainty_colors[4], marker='s', label='FEE Opt 5', linewidth=1)
ax1.plot(FEEOpt10_pp1[:, 0], FEEOpt10_pp1[:, 1], color=uncertainty_colors[6], marker='D', label='FEE Opt 10', linewidth=1)

for tick in ax1.get_xticklabels():
    tick.set_fontname("serif")
for tick in ax1.get_yticklabels():
    tick.set_fontname("serif")

ax1.set_ylabel(r'Thermal Comfort$^{-1}$', fontdict=axfontsm)
ax1.set_xlabel('HVAC Power', fontdict=axfontsm)
ax1.set_title(r'Trial 1', fontdict=titlefontsm)

ax1.set_ylim([2, 15])
ax1.set_xlim([6.75, 10.5])

lines, labels = ax1.get_legend_handles_labels()
legend = fig1.legend(lines, labels, loc='upper center', bbox_to_anchor=(0.525, 1.0),
          ncol=5, fancybox=True, shadow=False, prop=legendfontsm, bbox_transform=plt.gcf().transFigure)
legend.set_in_layout(True)

'''Trial 2 for all uncertainty sets'''
ax2.plot(Baseline_pp2[:, 0], Baseline_pp2[:, 1], color='k', marker='.', label='Baseline', linewidth=1)
ax2.plot(PMVOpt5_pp2[:, 0], PMVOpt5_pp2[:, 1], color=uncertainty_colors[2], marker='+', label='PMV Opt 5', linewidth=1)
ax2.plot(PMVOpt10_pp2[:, 0], PMVOpt10_pp2[:, 1], color=uncertainty_colors[0], marker='x', label='PMV Opt 10', linewidth=1)
ax2.plot(FEEOpt5_pp2[:, 0], FEEOpt5_pp2[:, 1], color=uncertainty_colors[4], marker='s', label='FEE Opt 5', linewidth=1)
ax2.plot(FEEOpt10_pp2[:, 0], FEEOpt10_pp2[:, 1], color=uncertainty_colors[6], marker='D', label='FEE Opt 10', linewidth=1)

for tick in ax2.get_xticklabels():
    tick.set_fontname("serif")
for tick in ax2.get_yticklabels():
    tick.set_fontname("serif")

ax2.set_ylabel(r'Thermal Comfort$^{-1}$', fontdict=axfontsm)
ax2.set_xlabel('HVAC Power', fontdict=axfontsm)
ax2.set_title(r'Trial 2', fontdict=titlefontsm)

ax2.set_ylim([2, 15])
ax2.set_xlim([6.75, 10.5])

# ax2.legend(loc='upper center', bbox_to_anchor=(0.5, 1.0),
#           ncol=4, fancybox=True, shadow=False, prop=legendfontsm)

'''Trial 3 for all uncertainty sets'''
ax3.plot(Baseline_pp3[:, 0], Baseline_pp3[:, 1], color='k', marker='.', label='Baseline', linewidth=1)
ax3.plot(PMVOpt5_pp3[:, 0], PMVOpt5_pp3[:, 1], color=uncertainty_colors[2], marker='+', label='PMV Opt 5', linewidth=1)
ax3.plot(PMVOpt10_pp3[:, 0], PMVOpt10_pp3[:, 1], color=uncertainty_colors[0], marker='x', label='PMV Opt 10', linewidth=1)
ax3.plot(FEEOpt5_pp3[:, 0], FEEOpt5_pp3[:, 1], color=uncertainty_colors[4], marker='s', label='FEE Opt 5', linewidth=1)
ax3.plot(FEEOpt10_pp3[:, 0], FEEOpt10_pp3[:, 1], color=uncertainty_colors[6], marker='D', label='FEE Opt 10', linewidth=1)

for tick in ax3.get_xticklabels():
    tick.set_fontname("serif")
for tick in ax3.get_yticklabels():
    tick.set_fontname("serif")

ax3.set_ylabel(r'Thermal Comfort$^{-1}$', fontdict=axfontsm)
ax3.set_xlabel('HVAC Power', fontdict=axfontsm)
ax3.set_title(r'Trial 3', fontdict=titlefontsm)

ax3.set_ylim([2, 15])
ax3.set_xlim([6.75, 10.5])

# ax3.legend(loc='upper center', bbox_to_anchor=(0.5, 1.0),
#           ncol=4, fancybox=True, shadow=False, prop=legendfontsm)

'''Trial 4 for all uncertainty sets'''
ax4.plot(Baseline_pp4[:, 0], Baseline_pp4[:, 1], color='k', marker='.', label='Baseline', linewidth=1)
ax4.plot(PMVOpt5_pp4[:, 0], PMVOpt5_pp4[:, 1], color=uncertainty_colors[2], marker='+', label='PMV Opt 5', linewidth=1)
ax4.plot(PMVOpt10_pp4[:, 0], PMVOpt10_pp4[:, 1], color=uncertainty_colors[0], marker='x', label='PMV Opt 10', linewidth=1)
ax4.plot(FEEOpt5_pp4[:, 0], FEEOpt5_pp4[:, 1], color=uncertainty_colors[4], marker='s', label='FEE Opt 5', linewidth=1)
ax4.plot(FEEOpt10_pp4[:, 0], FEEOpt10_pp4[:, 1], color=uncertainty_colors[6], marker='D', label='FEE Opt 10', linewidth=1)

for tick in ax4.get_xticklabels():
    tick.set_fontname("serif")
for tick in ax4.get_yticklabels():
    tick.set_fontname("serif")

ax4.set_ylabel(r'Thermal Comfort$^{-1}$', fontdict=axfontsm)
ax4.set_xlabel('HVAC Power', fontdict=axfontsm)
ax4.set_title(r'Trial 4', fontdict=titlefontsm)

ax4.set_ylim([2, 15])
ax4.set_xlim([6.75, 10.5])

plt.savefig(figurename)

# ax1.legend(loc='upper center', bbox_to_anchor=(0.5, 1.0),
#           ncol=4, fancybox=True, shadow=False, prop=legendfontsm)



# fig = plt.figure()
# ax = fig.add_subplot(111)
# dp = np.array(list(dominatedPoints))
# pp = np.array(list(paretoPoints))
# print(pp.shape,dp.shape)
# ax.scatter(dp[:,0],dp[:,1])
# ax.scatter(pp[:,0],pp[:,1],color='red')

# import matplotlib.tri as mtri
# triang = mtri.Triangulation(pp[:,0],pp[:,1])
# ax.plot_trisurf(triang,pp[:,2],color='red')
# plt.show()

plt.show()