'''
Kaden Plewe
3/5/2019
Optimization Model for SEB Single Thermal Zone Building

This will define an optimization problem based on the small office EnergyPlus model. It will be passed into
the optimization algorithm directly.
idf location: C:\Users\Owner\OneDrive\Research\Masters Thesis\Open Studio\Building Models
idd location: C:\EnergyPlusV8-5-0\Energy+.idd
eppy location: C:\Users\Owner\Anaconda3\Lib\site-packages\eppy
'''

'''import libraries'''
from SmallOfficeModules import configuresmalloffice, smallofficeoutputs
from eppy.modeleditor import IDF
import eppy.json_functions as json_functions
import os
import json
import csv
from collections import defaultdict
import numpy as np
from platypus import Problem, Real
import random
# OptCS = "global"; OptCS = []; OptHS = "global"; OptHS = []
'''parameter set used to apply uncertainty'''
# with open('jsonOUTPUT_PMVOpt10.txt') as jsonParams:
#     paramSet = json.load(jsonParams)

paramSet = {'input': []}

'''optimization problem for hour 1 of 24'''
class SO1(Problem):

    def __init__(self, Begin_Month, Begin_Day_of_Month, End_Month, End_Day_of_Month):
        '''define SEB problem as having 30 decision variables (Space Thermostat HTG and CLG Setpoint), 2 objective
        (HVAC Demand + PMV) and 48 constraints (PMV values and derivatives)'''
        super(SO1, self).__init__(48, 3, 48)

        '''define the two decision variables as real values with limited ranges
           30 total variables for heating and cooling setpoints for a 24 hour period'''
        self.types[:] = [Real(23.5, 30), Real(23.5, 30), Real(23.5, 30), Real(23.5, 30), Real(23.5, 30), Real(23.5, 30),
                         Real(23.5, 30), Real(23.5, 30), Real(23.5, 30), Real(23.5, 30), Real(23.5, 30), Real(23.5, 30),
                         Real(23.5, 30), Real(23.5, 30), Real(23.5, 30), Real(23.5, 30), Real(23.5, 30), Real(23.5, 30),
                         Real(23.5, 30), Real(23.5, 30), Real(23.5, 30), Real(23.5, 30), Real(23.5, 30), Real(23.5, 30),
                         Real(15.5, 23), Real(15.5, 23), Real(15.5, 23), Real(15.5, 23), Real(15.5, 23), Real(15.5, 23),
                         Real(15.5, 23), Real(15.5, 23), Real(15.5, 23), Real(15.5, 23), Real(15.5, 23), Real(15.5, 23),
                         Real(15.5, 23), Real(15.5, 23), Real(15.5, 23), Real(15.5, 23), Real(15.5, 23), Real(15.5, 23),
                         Real(15.5, 23), Real(15.5, 23), Real(15.5, 23), Real(15.5, 23), Real(15.5, 23), Real(15.5, 23)]

        '''define the types of constraints that will be used in the problem definition'''
        self.constraints[:] = "<=0"

        '''introduce the necessary files for the building simulation'''
        self.iddfile = "C:\EnergyPlusV8-5-0\Energy+.idd"
        self.fname = "SmallOffice.idf"
        self.weatherfile = "USA_MI_Lansing-Capital.City.AP.725390_TMY3.epw"

        '''initialize idf file'''
        IDF.setiddname(self.iddfile)
        self.idfdevice = IDF(self.fname, self.weatherfile)

        '''initialize idf file for specified outputs and simulation period'''
        '''update the run period fields'''
        for object in self.idfdevice.idfobjects['RUNPERIOD']:
            object.Begin_Month = Begin_Month
            object.Begin_Day_of_Month = Begin_Day_of_Month
            object.End_Month = End_Month
            object.End_Day_of_Month = End_Day_of_Month

        '''update the simulation control variables'''
        for object in self.idfdevice.idfobjects['SIMULATIONCONTROL']:
            object.Do_Zone_Sizing_Calculation = 'Yes'
            object.Do_System_Sizing_Calculation = 'Yes'
            object.Do_Plant_Sizing_Calculation = 'Yes'
            object.Run_Simulation_for_Sizing_Periods = 'No'
            object.Run_Simulation_for_Weather_File_Run_Periods = 'Yes'
            print('=== Sumulation Control Parameters Changed ===')

        '''add thermal comfort model to people objects'''
        for object in self.idfdevice.idfobjects['PEOPLE']:
            object.Surface_NameAngle_Factor_List_Name = ''
            object.Work_Efficiency_Schedule_Name = 'WORK_EFF_SCH'
            object.Clothing_Insulation_Schedule_Name = 'CLOTHING_SCH'
            object.Air_Velocity_Schedule_Name = 'AIR_VELO_SCH'
            object.Thermal_Comfort_Model_1_Type = 'Fanger'

        '''Fanger PMV thermal comfort model (Zone Average)'''
        self.idfdevice.newidfobject('OUTPUT:VARIABLE')
        self.idfdevice.idfobjects['OUTPUT:VARIABLE'][-1].Variable_Name = 'Zone Thermal Comfort Fanger Model PMV'
        self.idfdevice.idfobjects['OUTPUT:VARIABLE'][-1].Reporting_Frequency = 'Hourly'

        '''Fanger PPD thermal comfort model (Zone Average)'''
        self.idfdevice.newidfobject('OUTPUT:VARIABLE')
        self.idfdevice.idfobjects['OUTPUT:VARIABLE'][-1].Variable_Name = 'Zone Thermal Comfort Fanger Model PPD'
        self.idfdevice.idfobjects['OUTPUT:VARIABLE'][-1].Reporting_Frequency = 'Hourly'

        '''Total Purchase Electric Energy [J]'''
        self.idfdevice.newidfobject('OUTPUT:VARIABLE')
        self.idfdevice.idfobjects['OUTPUT:VARIABLE'][-1].Variable_Name = 'Facility Total Purchased Electric Energy'
        self.idfdevice.idfobjects['OUTPUT:VARIABLE'][-1].Reporting_Frequency = 'Hourly'

        '''Total HVAC Demand [W]'''
        self.idfdevice.newidfobject('OUTPUT:VARIABLE')
        self.idfdevice.idfobjects['OUTPUT:VARIABLE'][-1].Variable_Name = 'Facility Total HVAC Electric Demand Power'
        self.idfdevice.idfobjects['OUTPUT:VARIABLE'][-1].Reporting_Frequency = 'Hourly'

        '''Hourly cooling temperature setpoint [°C]'''
        self.idfdevice.newidfobject('OUTPUT:VARIABLE')
        self.idfdevice.idfobjects['OUTPUT:VARIABLE'][-1].Variable_Name = 'Zone Thermostat Cooling Setpoint Temperature'
        self.idfdevice.idfobjects['OUTPUT:VARIABLE'][-1].Reporting_Frequency = 'Hourly'

        '''Hourly heating temperature setpoint [°C]'''
        self.idfdevice.newidfobject('OUTPUT:VARIABLE')
        self.idfdevice.idfobjects['OUTPUT:VARIABLE'][-1].Variable_Name = 'Zone Thermostat Heating Setpoint Temperature'
        self.idfdevice.idfobjects['OUTPUT:VARIABLE'][-1].Reporting_Frequency = 'Hourly'

        '''Zone thermostat air temperature [°C]'''
        self.idfdevice.newidfobject('OUTPUT:VARIABLE')
        self.idfdevice.idfobjects['OUTPUT:VARIABLE'][-1].Variable_Name = 'Zone Thermostat Air Temperature'
        self.idfdevice.idfobjects['OUTPUT:VARIABLE'][-1].Reporting_Frequency = 'Hourly'



    def evaluate(self, solution):
        self.CSP1 = solution.variables[0]
        self.CSP2 = solution.variables[1]
        self.CSP3 = solution.variables[2]
        self.CSP4 = solution.variables[3]
        self.CSP5 = solution.variables[4]
        self.CSP6 = solution.variables[5]
        self.CSP7 = solution.variables[6]
        self.CSP8 = solution.variables[7]
        self.CSP9 = solution.variables[8]
        self.CSP10 = solution.variables[9]
        self.CSP11 = solution.variables[10]
        self.CSP12 = solution.variables[11]
        self.CSP13 = solution.variables[12]
        self.CSP14 = solution.variables[13]
        self.CSP15 = solution.variables[14]
        self.CSP16 = solution.variables[15]
        self.CSP17 = solution.variables[16]
        self.CSP18 = solution.variables[17]
        self.CSP19 = solution.variables[18]
        self.CSP20 = solution.variables[19]
        self.CSP21 = solution.variables[20]
        self.CSP22 = solution.variables[21]
        self.CSP23 = solution.variables[22]
        self.CSP24 = solution.variables[23]
        self.HSP1 = solution.variables[24]
        self.HSP2 = solution.variables[25]
        self.HSP3 = solution.variables[26]
        self.HSP4 = solution.variables[27]
        self.HSP5 = solution.variables[28]
        self.HSP6 = solution.variables[29]
        self.HSP7 = solution.variables[30]
        self.HSP8 = solution.variables[31]
        self.HSP9 = solution.variables[32]
        self.HSP10 = solution.variables[33]
        self.HSP11 = solution.variables[34]
        self.HSP12 = solution.variables[35]
        self.HSP13 = solution.variables[36]
        self.HSP14 = solution.variables[37]
        self.HSP15 = solution.variables[38]
        self.HSP16 = solution.variables[39]
        self.HSP17 = solution.variables[40]
        self.HSP18 = solution.variables[41]
        self.HSP19 = solution.variables[42]
        self.HSP20 = solution.variables[43]
        self.HSP21 = solution.variables[44]
        self.HSP22 = solution.variables[45]
        self.HSP23 = solution.variables[46]
        self.HSP24 = solution.variables[47]
        self.results = buildingSim(self.idfdevice, [self.CSP1, self.CSP2, self.CSP3, self.CSP4, self.CSP5, self.CSP6,
                                                    self.CSP7, self.CSP8, self.CSP9, self.CSP10, self.CSP11, self.CSP12,
                                                    self.CSP13, self.CSP14, self.CSP15, self.CSP16, self.CSP17, self.CSP18,
                                                    self.CSP19, self.CSP20, self.CSP21, self.CSP22, self.CSP23, self.CSP24],
                                                    [self.HSP1, self.HSP2, self.HSP3, self.HSP4, self.HSP5, self.HSP6,
                                                     self.HSP7, self.HSP8, self.HSP9, self.HSP10, self.HSP11, self.HSP12,
                                                     self.HSP13, self.HSP14, self.HSP15, self.HSP16, self.HSP17, self.HSP18,
                                                     self.HSP19, self.HSP20, self.HSP21, self.HSP22, self.HSP23, self.HSP24])
        print('=== hvacPower_ave = %f ===' % self.results.hvacPower_ave)
        print('=== allPMV_max = %f ===' % self.results.allPMV_max)
        print('=== allPMV_min = %f ===' % self.results.allPMV_min)

        '''matrix that extracts pmv values for working hours'''
        pmvI = np.identity(48)
        pmvA = np.identity(48)*5
        # offHours = [0, 1, 2, 3, 4, 5, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37,
        #             38, 39, 40, 41, 42, 43, 44, 45, 46, 47]
        offHours = [0, 1, 2, 3, 4, 5, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 42, 43, 44, 45, 46, 47]
        # offHours = [0, 1, 2, 3, 4, 5, 18, 19, 20, 21, 22, 23]
        for i in offHours:
            pmvI[i, i] = 0
            pmvA[i, i] = 0

        '''matrix for hvac power weight'''
        hvacA = np.identity(48)*0.0000001

        '''matrix for applying derivative constraint'''
        diagonal = np.array([1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0,
                             1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1])
        D = np.diag(diagonal, 1)

        setpoints = np.array([self.CSP1, self.CSP2, self.CSP3, self.CSP4, self.CSP5, self.CSP6, self.CSP7, self.CSP8,
                              self.CSP9, self.CSP10, self.CSP11, self.CSP12, self.CSP13, self.CSP14, self.CSP15,
                              self.CSP16, self.CSP17, self.CSP18, self.CSP19, self.CSP20, self.CSP21, self.CSP22,
                              self.CSP23, self.CSP24,
                              self.HSP1, self.HSP2, self.HSP3, self.HSP4, self.HSP5, self.HSP6, self.HSP7, self.HSP8,
                              self.HSP9, self.HSP10, self.HSP11, self.HSP12, self.HSP13, self.HSP14, self.HSP15,
                              self.HSP16, self.HSP17, self.HSP18, self.HSP19, self.HSP20, self.HSP21, self.HSP22,
                              self.HSP23, self.HSP24])

        '''matrix for changing setpoint downwards cost'''
        constDownA = np.identity(48)*0.05

        constrainDown = setpoints.T - D@setpoints.T

        print(constrainDown)


        print('objective 1: %f' % (self.results.hvacPower[0:48]@hvacA@self.results.hvacPower[0:48].T))
        print('objective 2: %f' % (self.results.allPMV_mean1[0, 0:48]@pmvA@self.results.allPMV_mean1[0, 0:48].T))
        print('objective 3: %f' % (constrainDown@constDownA@constrainDown.T))

        '''hvac power demand and predicted mean vote objective function'''
        solution.objectives[0] = np.sqrt((self.results.hvacPower[0:48]@hvacA@self.results.hvacPower[0:48].T))
        solution.objectives[1] =  np.sqrt((self.results.allPMV_mean1[0, 0:48]@pmvA@self.results.allPMV_mean1[0, 0:48].T))
        solution.objectives[2] = np.sqrt((constrainDown@constDownA@constrainDown.T))

        '''thermal comfort constraints'''
        solution.constraints[:] = abs(pmvI@self.results.allPMV_mean1[0, 0:48].T) - 1

'''optimization problem for a single set point temperature (for simplicity)'''
class SO2(Problem):

    def __init__(self, Begin_Month, Begin_Day_of_Month, End_Month, End_Day_of_Month):
        '''define SEB problem as having 2 decision variables (Space Thermostat HTG and CLG Setpoint), 2 objective
        (HVAC Demand + PMV) and 48 constraints (PMV values and derivatives)'''
        super(SO2, self).__init__(2, 2, 48)

        '''define the two decision variables as real values with limited ranges
           30 total variables for heating and cooling setpoints for a 24 hour period'''
        self.types[:] = [Real(23.5, 30), Real(15.5, 23)]

        '''define the types of constraints that will be used in the problem definition'''
        self.constraints[:] = "<=0"

        '''introduce the necessary files for the building simulation'''
        self.iddfile = "C:\EnergyPlusV8-5-0\Energy+.idd"
        self.fname = "SmallOffice.idf"
        self.weatherfile = "USA_MI_Lansing-Capital.City.AP.725390_TMY3.epw"

        '''initialize idf file'''
        IDF.setiddname(self.iddfile)
        self.idfdevice = IDF(self.fname, self.weatherfile)

        '''initialize idf file for specified outputs and simulation period'''
        '''update the run period fields'''
        for object in self.idfdevice.idfobjects['RUNPERIOD']:
            object.Begin_Month = Begin_Month
            object.Begin_Day_of_Month = Begin_Day_of_Month
            object.End_Month = End_Month
            object.End_Day_of_Month = End_Day_of_Month

        '''update the simulation control variables'''
        for object in self.idfdevice.idfobjects['SIMULATIONCONTROL']:
            object.Do_Zone_Sizing_Calculation = 'Yes'
            object.Do_System_Sizing_Calculation = 'Yes'
            object.Do_Plant_Sizing_Calculation = 'Yes'
            object.Run_Simulation_for_Sizing_Periods = 'No'
            object.Run_Simulation_for_Weather_File_Run_Periods = 'Yes'
            print('=== Sumulation Control Parameters Changed ===')

        '''add thermal comfort model to people objects'''
        for object in self.idfdevice.idfobjects['PEOPLE']:
            object.Surface_NameAngle_Factor_List_Name = ''
            object.Work_Efficiency_Schedule_Name = 'WORK_EFF_SCH'
            object.Clothing_Insulation_Schedule_Name = 'CLOTHING_SCH'
            object.Air_Velocity_Schedule_Name = 'AIR_VELO_SCH'
            object.Thermal_Comfort_Model_1_Type = 'Fanger'

        '''Fanger PMV thermal comfort model (Zone Average)'''
        self.idfdevice.newidfobject('OUTPUT:VARIABLE')
        self.idfdevice.idfobjects['OUTPUT:VARIABLE'][-1].Variable_Name = 'Zone Thermal Comfort Fanger Model PMV'
        self.idfdevice.idfobjects['OUTPUT:VARIABLE'][-1].Reporting_Frequency = 'Hourly'

        '''Fanger PPD thermal comfort model (Zone Average)'''
        self.idfdevice.newidfobject('OUTPUT:VARIABLE')
        self.idfdevice.idfobjects['OUTPUT:VARIABLE'][-1].Variable_Name = 'Zone Thermal Comfort Fanger Model PPD'
        self.idfdevice.idfobjects['OUTPUT:VARIABLE'][-1].Reporting_Frequency = 'Hourly'

        '''Total Purchase Electric Energy [J]'''
        self.idfdevice.newidfobject('OUTPUT:VARIABLE')
        self.idfdevice.idfobjects['OUTPUT:VARIABLE'][-1].Variable_Name = 'Facility Total Purchased Electric Energy'
        self.idfdevice.idfobjects['OUTPUT:VARIABLE'][-1].Reporting_Frequency = 'Hourly'

        '''Total HVAC Demand [W]'''
        self.idfdevice.newidfobject('OUTPUT:VARIABLE')
        self.idfdevice.idfobjects['OUTPUT:VARIABLE'][-1].Variable_Name = 'Facility Total HVAC Electric Demand Power'
        self.idfdevice.idfobjects['OUTPUT:VARIABLE'][-1].Reporting_Frequency = 'Hourly'

        '''Hourly cooling temperature setpoint [°C]'''
        self.idfdevice.newidfobject('OUTPUT:VARIABLE')
        self.idfdevice.idfobjects['OUTPUT:VARIABLE'][-1].Variable_Name = 'Zone Thermostat Cooling Setpoint Temperature'
        self.idfdevice.idfobjects['OUTPUT:VARIABLE'][-1].Reporting_Frequency = 'Hourly'

        '''Hourly heating temperature setpoint [°C]'''
        self.idfdevice.newidfobject('OUTPUT:VARIABLE')
        self.idfdevice.idfobjects['OUTPUT:VARIABLE'][-1].Variable_Name = 'Zone Thermostat Heating Setpoint Temperature'
        self.idfdevice.idfobjects['OUTPUT:VARIABLE'][-1].Reporting_Frequency = 'Hourly'

        '''Zone thermostat air temperature [°C]'''
        self.idfdevice.newidfobject('OUTPUT:VARIABLE')
        self.idfdevice.idfobjects['OUTPUT:VARIABLE'][-1].Variable_Name = 'Zone Thermostat Air Temperature'
        self.idfdevice.idfobjects['OUTPUT:VARIABLE'][-1].Reporting_Frequency = 'Hourly'



    def evaluate(self, solution):
        self.CSP1 = solution.variables[0]
        self.HSP1 = solution.variables[1]
        self.results = buildingSim(self.idfdevice, [self.CSP1],
                                                    [self.HSP1])
        print('=== hvacPower_ave = %f ===' % self.results.hvacPower_ave)
        print('=== allPMV_max = %f ===' % self.results.allPMV_max)
        print('=== allPMV_min = %f ===' % self.results.allPMV_min)

        '''matrix that extracts pmv values for working hours'''
        pmvI = np.identity(48)
        pmvA = np.identity(48)*5
        # offHours = [0, 1, 2, 3, 4, 5, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37,
        #             38, 39, 40, 41, 42, 43, 44, 45, 46, 47]
        offHours = [0, 1, 2, 3, 4, 5, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 42, 43, 44, 45, 46, 47]
        # offHours = [0, 1, 2, 3, 4, 5, 18, 19, 20, 21, 22, 23]
        for i in offHours:
            pmvI[i, i] = 0
            pmvA[i, i] = 0

        '''matrix for hvac power weight'''
        hvacA = np.identity(48)*0.0000001

        '''matrix for applying derivative constraint'''
        # diagonal = np.array([1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0,
        #                      1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1])
        # D = np.diag(diagonal, 1)

        # setpoints = np.array([self.CSP1,
        #                       self.HSP1])

        '''matrix for changing setpoint downwards cost'''
        # constDownA = np.identity(48)*0.05

        # constrainDown = setpoints.T - D@setpoints.T

        # print(constrainDown)


        print('objective 1: %f' % (self.results.hvacPower[0:48]@hvacA@self.results.hvacPower[0:48].T))
        print('objective 2: %f' % (self.results.allPMV_mean1[0, 0:48]@pmvA@self.results.allPMV_mean1[0, 0:48].T))
        # print('objective 3: %f' % (constrainDown@constDownA@constrainDown.T))

        '''hvac power demand and predicted mean vote objective function'''
        solution.objectives[0] = np.sqrt((self.results.hvacPower[0:48]@hvacA@self.results.hvacPower[0:48].T))
        solution.objectives[1] =  np.sqrt((self.results.allPMV_mean1[0, 0:48]@pmvA@self.results.allPMV_mean1[0, 0:48].T))
        # solution.objectives[2] = np.sqrt((constrainDown@constDownA@constrainDown.T))

        '''thermal comfort constraints'''
        solution.constraints[:] = abs(pmvI@self.results.allPMV_mean1[0, 0:48].T) - 1

class buildingSim:
    def __init__(self, idfdevice, CLG_SETPOINT, HTG_SETPOINT):
        '''update setpoints and run energyplus simulation'''

        '''append setpoints from optimizer to the optimized list'''
        # OptCS[(24 - len(CLG_SETPOINT)):] = CLG_SETPOINT
        # OptHS[(24 - len(HTG_SETPOINT)):] = HTG_SETPOINT

        '''update idf with uncertain parameters for the parameter file listed'''
        runJSON = {}
        for object in paramSet['input']: runJSON[object['eppy json string']] = object['Sample Values'][random.randint(0, len(object['Sample Values'])-1)]
        json_functions.updateidf(idfdevice, runJSON)

        '''modify idf with inputs'''
        self.runJSON = {'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_1': 'Through: %s/%s' % ('12', '31'),
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_2': 'For: Weekday',
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_3': 'Until: 1:00',
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_4': str(CLG_SETPOINT[0]),
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_5': 'Until: 2:00',
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_6': str(CLG_SETPOINT[0]),
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_7': 'Until: 3:00',
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_8': str(CLG_SETPOINT[0]),
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_9': 'Until: 4:00',
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_10': str(CLG_SETPOINT[0]),
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_11': 'Until: 5:00',
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_12': str(CLG_SETPOINT[0]),
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_13': 'Until: 6:00',
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_14': str(CLG_SETPOINT[0]),
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_15': 'Until: 7:00',
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_16': str(CLG_SETPOINT[0]),
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_17': 'Until: 8:00',
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_18': str(CLG_SETPOINT[0]),
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_19': 'Until: 9:00',
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_20': str(CLG_SETPOINT[0]),
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_21': 'Until: 10:00',
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_22': str(CLG_SETPOINT[0]),
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_23': 'Until: 11:00',
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_24': str(CLG_SETPOINT[0]),
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_25': 'Until: 12:00',
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_26': str(CLG_SETPOINT[0]),
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_27': 'Until: 13:00',
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_28': str(CLG_SETPOINT[0]),
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_29': 'Until: 14:00',
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_30': str(CLG_SETPOINT[0]),
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_31': 'Until: 15:00',
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_32': str(CLG_SETPOINT[0]),
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_33': 'Until: 16:00',
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_34': str(CLG_SETPOINT[0]),
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_35': 'Until: 17:00',
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_36': str(CLG_SETPOINT[0]),
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_37': 'Until: 18:00',
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_38': str(CLG_SETPOINT[0]),
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_39': 'Until: 19:00',
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_40': str(CLG_SETPOINT[0]),
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_41': 'Until: 20:00',
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_42': str(CLG_SETPOINT[0]),
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_43': 'Until: 21:00',
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_44': str(CLG_SETPOINT[0]),
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_45': 'Until: 22:00',
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_46': str(CLG_SETPOINT[0]),
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_47': 'Until: 23:00',
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_48': str(CLG_SETPOINT[0]),
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_49': 'Until: 24:00',
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_50': str(CLG_SETPOINT[0]),
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_51': 'For: Weekend',
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_52': 'Until: 24:00',
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_53': str(29.44),
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_54': 'For: Holiday',
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_55': 'Until: 24:00',
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_56': str(29.44),
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_57': 'For: WinterDesignDay',
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_58': 'Until: 24:00',
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_59': str(29.44),
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_60': 'For: SummerDesignDay',
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_61': 'Until: 24:00',
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_62': str(29.44),
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_63': 'For: CustomDay1',
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_64': 'Until: 24:00',
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_65': str(29.44),
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_66': 'For: CustomDay2',
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_67': 'Until: 24:00',
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_68': str(29.44),
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_1': 'Through: %s/%s' % ('12', '31'),
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_2': 'For: Weekday',
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_3': 'Until: 1:00',
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_4': str(HTG_SETPOINT[0]),
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_5': 'Until: 2:00',
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_6': str(HTG_SETPOINT[0]),
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_7': 'Until: 3:00',
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_8': str(HTG_SETPOINT[0]),
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_9': 'Until: 4:00',
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_10': str(HTG_SETPOINT[0]),
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_11': 'Until: 5:00',
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_12': str(HTG_SETPOINT[0]),
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_13': 'Until: 6:00',
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_14': str(HTG_SETPOINT[0]),
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_15': 'Until: 7:00',
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_16': str(HTG_SETPOINT[0]),
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_17': 'Until: 8:00',
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_18': str(HTG_SETPOINT[0]),
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_19': 'Until: 9:00',
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_20': str(HTG_SETPOINT[0]),
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_21': 'Until: 10:00',
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_22': str(HTG_SETPOINT[0]),
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_23': 'Until: 11:00',
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_24': str(HTG_SETPOINT[0]),
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_25': 'Until: 12:00',
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_26': str(HTG_SETPOINT[0]),
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_27': 'Until: 13:00',
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_28': str(HTG_SETPOINT[0]),
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_29': 'Until: 14:00',
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_30': str(HTG_SETPOINT[0]),
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_31': 'Until: 15:00',
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_32': str(HTG_SETPOINT[0]),
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_33': 'Until: 16:00',
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_34': str(HTG_SETPOINT[0]),
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_35': 'Until: 17:00',
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_36': str(HTG_SETPOINT[0]),
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_37': 'Until: 18:00',
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_38': str(HTG_SETPOINT[0]),
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_39': 'Until: 19:00',
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_40': str(HTG_SETPOINT[0]),
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_41': 'Until: 20:00',
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_42': str(HTG_SETPOINT[0]),
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_43': 'Until: 21:00',
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_44': str(HTG_SETPOINT[0]),
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_45': 'Until: 22:00',
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_46': str(HTG_SETPOINT[0]),
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_47': 'Until: 23:00',
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_48': str(HTG_SETPOINT[0]),
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_49': 'Until: 24:00',
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_50': str(HTG_SETPOINT[0]),
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_51': 'For: Weekend',
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_52': 'Until: 24:00',
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_53': str(29.44),
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_54': 'For: Holiday',
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_55': 'Until: 24:00',
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_56': str(29.44),
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_57': 'For: WinterDesignDay',
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_58': 'Until: 24:00',
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_59': str(29.44),
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_60': 'For: SummerDesignDay',
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_61': 'Until: 24:00',
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_62': str(29.44),
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_63': 'For: CustomDay1',
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_64': 'Until: 24:00',
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_65': str(29.44),
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_66': 'For: CustomDay2',
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_67': 'Until: 24:00',
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_68': str(29.44)
                        }

        json_functions.updateidf(idfdevice, self.runJSON)

        '''run IDF and the associated batch file to export the custom csv output'''
        '''self, idf='SmallOffice.idf', weather='USA_UT_Salt.Lake.City.Intl.AP.725720_TMY3.epw', ep_version='8-5-0'''
        idfdevice.run(verbose='q')
        os.system(r'CD E:\Masters Thesis\EnergyPlus MPC\Simulations\Baseline')
        os.system('CustomCSV SO OUTPUT')

        # self.smallofficeoutputs('SO_OUTPUT_hourly.csv')

        '''Read csv file into new data dictionary'''
        newEntry = defaultdict(list)
        with open('SO_OUTPUT_hourly.csv', newline='') as newFile:
            newData = csv.DictReader(newFile)
            for row in newData:
                [newEntry[key].append(value) for key, value in row.items()]

        '''Date/Time array'''
        self.DateTime = np.asarray(newEntry['Date/Time'], dtype=str)

        '''Outdoor dry bulb temperature'''
        self.outdoorT = np.asarray(newEntry['Environment:Site Outdoor Air Drybulb Temperature [C](Hourly)'],
                                  dtype=np.float32)

        '''PMV values for core zone'''
        self.corePMV = np.asarray(newEntry['CORE_ZN:Zone Thermal Comfort Fanger Model PMV [](Hourly)'],
                                  dtype=np.float32)
        self.corePMV_mean = np.mean(self.corePMV)
        self.corePMV_max = np.max(self.corePMV)
        self.corePMV_min = np.min(self.corePMV)

        '''PMV values for zone 1'''
        self.zn1PMV = np.asarray(newEntry['PERIMETER_ZN_1:Zone Thermal Comfort Fanger Model PMV [](Hourly)'],
                                 dtype=np.float32)
        self.zn1PMV_mean = np.mean(self.zn1PMV)
        self.zn1PMV_max = np.max(self.zn1PMV)
        self.zn1PMV_min = np.min(self.zn1PMV)

        '''PMV values for zone 2'''
        self.zn2PMV = np.asarray(newEntry['PERIMETER_ZN_2:Zone Thermal Comfort Fanger Model PMV [](Hourly)'],
                                 dtype=np.float32)
        self.zn2PMV_mean = np.mean(self.zn2PMV)
        self.zn2PMV_max = np.max(self.zn2PMV)
        self.zn2PMV_min = np.min(self.zn2PMV)

        '''PMV values for zone 3'''
        self.zn3PMV = np.asarray(newEntry['PERIMETER_ZN_3:Zone Thermal Comfort Fanger Model PMV [](Hourly)'],
                                 dtype=np.float32)
        self.zn3PMV_mean = np.mean(self.zn3PMV)
        self.zn3PMV_max = np.max(self.zn3PMV)
        self.zn3PMV_min = np.min(self.zn3PMV)

        '''PMV values for zone 4'''
        self.zn4PMV = np.asarray(newEntry['PERIMETER_ZN_4:Zone Thermal Comfort Fanger Model PMV [](Hourly)'],
                                 dtype=np.float32)
        self.zn4PMV_mean = np.mean(self.zn4PMV)
        self.zn4PMV_max = np.max(self.zn4PMV)
        self.zn4PMV_min = np.min(self.zn4PMV)

        '''PMV values for all zones'''
        self.allPMV = np.asarray([[self.corePMV], [self.zn1PMV], [self.zn2PMV], [self.zn3PMV], [self.zn4PMV]])
        self.allPMV_mean1 = np.mean(self.allPMV, 0)
        self.allPMV_mean2 = np.mean(self.allPMV_mean1)
        self.allPMV_max = np.amax(self.allPMV)
        self.allPMV_min = np.amin(self.allPMV)

        '''HVAC power demand (kW)'''
        self.hvacPower = np.asarray(newEntry['Whole Building:Facility Total HVAC Electric Demand Power [W](Hourly)'],
                                     dtype=np.float32)
        self.hvacPower_ave = np.mean(self.hvacPower)
        self.hvacPower_max = np.max(self.hvacPower)

        '''Core Zone Cooling Setpoint (C)'''
        self.coreCS = np.asarray(newEntry['CORE_ZN:Zone Thermostat Cooling Setpoint Temperature [C](Hourly)'],
                                       dtype=np.float32)
        self.coreCS_mean = np.mean(self.coreCS)
        self.coreCS_max = np.max(self.coreCS)
        self.coreCS_min = np.min(self.coreCS)

        '''Zone 1 Cooling Setpoint (C)'''
        self.zn1CS = np.asarray(newEntry['PERIMETER_ZN_1:Zone Thermostat Cooling Setpoint Temperature [C](Hourly)'],
                       dtype=np.float32)
        self.zn1CS_mean = np.mean(self.zn1CS)
        self.zn1CS_max = np.max(self.zn1CS)
        self.zn1CS_min = np.min(self.zn1CS)

        '''Zone 2 Cooling Setpoint (C)'''
        self.zn2CS = np.asarray(newEntry['PERIMETER_ZN_2:Zone Thermostat Cooling Setpoint Temperature [C](Hourly)'],
                       dtype=np.float32)
        self.zn2CS_mean = np.mean(self.zn2CS)
        self.zn2CS_max = np.max(self.zn2CS)
        self.zn2CS_min = np.min(self.zn2CS)

        '''Zone 3 Cooling Setpoint (C)'''
        self.zn3CS = np.asarray(newEntry['PERIMETER_ZN_3:Zone Thermostat Cooling Setpoint Temperature [C](Hourly)'],
                       dtype=np.float32)
        self.zn3CS_mean = np.mean(self.zn3CS)
        self.zn3CS_max = np.max(self.zn3CS)
        self.zn3CS_min = np.min(self.zn3CS)

        '''Zone 4 Cooling Setpoint (C)'''
        self.zn4CS = np.asarray(newEntry['PERIMETER_ZN_4:Zone Thermostat Cooling Setpoint Temperature [C](Hourly)'],
                       dtype=np.float32)
        self.zn4CS_mean = np.mean(self.zn4CS)
        self.zn4CS_max = np.max(self.zn4CS)
        self.zn4CS_min = np.min(self.zn4CS)

        '''All Zones Cooling Setpoint (C)'''
        self.allCS = np.asarray([[self.coreCS], [self.zn1CS], [self.zn2CS], [self.zn3CS], [self.zn4CS]])
        self.allCS_mean1 = np.mean(self.allCS, 1)
        self.allCS_mean2 = np.mean(self.allCS_mean1)
        self.allCS_max = np.max(self.allCS)
        self.allCS_min = np.min(self.allCS)

        '''Core Zone Heating Setpoint (C)'''
        self.coreHS = np.asarray(newEntry['CORE_ZN:Zone Thermostat Heating Setpoint Temperature [C](Hourly)'],
                                        dtype=np.float32)
        self.coreHS_mean = np.mean(self.coreHS)
        self.coreHS_max = np.max(self.coreHS)
        self.coreHS_min = np.min(self.coreHS)

        '''Zone 1 Heating Setpoint (C)'''
        self.zn1HS = np.asarray(newEntry['PERIMETER_ZN_1:Zone Thermostat Heating Setpoint Temperature [C](Hourly)'],
                       dtype=np.float32)
        self.zn1HS_mean = np.mean(self.zn1HS)
        self.zn1HS_max = np.max(self.zn1HS)
        self.zn1HS_min = np.min(self.zn1HS)

        '''Zone 2 Heating Setpoint (C)'''
        self.zn2HS = np.asarray(newEntry['PERIMETER_ZN_2:Zone Thermostat Heating Setpoint Temperature [C](Hourly)'],
                       dtype=np.float32)
        self.zn2HS_mean = np.mean(self.zn2HS)
        self.zn2HS_max = np.max(self.zn2HS)
        self.zn2HS_min = np.min(self.zn2HS)

        '''Zone 3 Heating Setpoint (C)'''
        self.zn3HS = np.asarray(newEntry['PERIMETER_ZN_3:Zone Thermostat Heating Setpoint Temperature [C](Hourly)'],
                       dtype=np.float32)
        self.zn3HS_mean = np.mean(self.zn3HS)
        self.zn3HS_max = np.max(self.zn3HS)
        self.zn3HS_min = np.min(self.zn3HS)

        '''Zone 4 Heating Setpoint (C)'''
        self.zn4HS = np.asarray(newEntry['PERIMETER_ZN_4:Zone Thermostat Heating Setpoint Temperature [C](Hourly)'],
                       dtype=np.float32)
        self.zn4HS_mean = np.mean(self.zn4HS)
        self.zn4HS_max = np.max(self.zn4HS)
        self.zn4HS_min = np.min(self.zn4HS)

        '''All Zones Heating Setpoint (C)'''
        self.allHS = np.asarray([[self.coreHS], [self.zn1HS], [self.zn2HS], [self.zn3HS], [self.zn4HS]])
        self.allHS_mean1 = np.mean(self.allHS, 1)
        self.allHS_mean2 = np.mean(self.allHS_mean1)
        self.allHS_max = np.max(self.allHS)
        self.allHS_min = np.min(self.allHS)

        '''Core Zone Thermostat Temperature (C)'''
        self.coreT = np.asarray(newEntry['CORE_ZN:Zone Thermostat Air Temperature [C](Hourly)'],
                                        dtype=np.float32)
        self.coreT_mean = np.mean(self.coreT)
        self.coreT_max = np.max(self.coreT)
        self.coreT_min = np.min(self.coreT)

        '''Zone 1 Thermostat Temperature (C)'''
        self.zn1T = np.asarray(newEntry['PERIMETER_ZN_1:Zone Thermostat Air Temperature [C](Hourly)'],
                       dtype=np.float32)
        self.zn1T_mean = np.mean(self.zn1T)
        self.zn1T_max = np.max(self.zn1T)
        self.zn1T_min = np.min(self.zn1T)

        '''Zone 2 Thermostat Temperature (C)'''
        self.zn2T = np.asarray(newEntry['PERIMETER_ZN_2:Zone Thermostat Air Temperature [C](Hourly)'],
                       dtype=np.float32)
        self.zn2T_mean = np.mean(self.zn2T)
        self.zn2T_max = np.max(self.zn2T)
        self.zn2T_min = np.min(self.zn2T)

        '''Zone 3 Thermostat Temperature (C)'''
        self.zn3T = np.asarray(newEntry['PERIMETER_ZN_3:Zone Thermostat Air Temperature [C](Hourly)'],
                       dtype=np.float32)
        self.zn3T_mean = np.mean(self.zn3T)
        self.zn3T_max = np.max(self.zn3T)
        self.zn3T_min = np.min(self.zn3T)

        '''Zone 4 Thermostat Temperature (C)'''
        self.zn4T = np.asarray(newEntry['PERIMETER_ZN_4:Zone Thermostat Air Temperature [C](Hourly)'],
                       dtype=np.float32)
        self.zn4T_mean = np.mean(self.zn4T)
        self.zn4T_max = np.max(self.zn4T)
        self.zn4T_min = np.min(self.zn4T)

        '''All Zones Thermostat Temperature (C)'''
        self.allT = np.asarray([[self.coreT], [self.zn1T], [self.zn2T], [self.zn3T], [self.zn4T]])
        self.allT_mean1 = np.mean(self.allT, 1)
        self.allT_mean2 = np.mean(self.allT_mean1)
        self.allT_max = np.max(self.allT)
        self.allT_min = np.min(self.allT)










