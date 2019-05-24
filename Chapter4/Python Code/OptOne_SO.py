############################################################
# Kaden Plewe
# 3/5/2019
# Optimization Model for SEB Single Thermal Zone Building
############################################################

# This will define an optimization problem based on the SEB Single Thermal Zone Building Model. It will be passed into
# the optimization algorithm directly.
# idf location: C:\Users\Owner\OneDrive\Research\Masters Thesis\Open Studio\Building Models
# idd location: C:\EnergyPlusV8-5-0\Energy+.idd
# eppy location: C:\Users\Owner\Anaconda3\Lib\site-packages\eppy

# import libraries
#################################################
from SmallOfficeModules import configuresmalloffice, smallofficeoutputs
from eppy.modeleditor import IDF
import eppy.json_functions as json_functions
import os
import csv
from collections import defaultdict
import numpy as np
from platypus import Problem, Real

# building model input output class
##################################################
class SO(Problem):

    def __init__(self, Begin_Month, Begin_Day_of_Month, End_Month, End_Day_of_Month):
        '''define SEB problem as having 30 decision variables (Space Thermostat HTG and CLG Setpoint), 1 objectives
        (Facility Electricity) and 2 constraints (PMV values)'''
        super(SO, self).__init__(30, 1, 2)

        '''define the two decision variables as real values with limited ranges
           30 total variables for heating and cooling setpoints for a 24 hour period'''
        self.types[:] = [Real(23.5, 30), Real(23.5, 30), Real(23.5, 30), Real(23.5, 30), Real(23.5, 30), Real(23.5, 30),
                         Real(23.5, 30), Real(23.5, 30), Real(23.5, 30), Real(23.5, 30), Real(23.5, 30), Real(23.5, 30),
                         Real(23.5, 30), Real(23.5, 30), Real(23.5, 30), Real(15.5, 23), Real(15.5, 23), Real(15.5, 23),
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

        self.idfdevice.newidfobject('OUTPUT:VARIABLE')
        self.idfdevice.idfobjects['OUTPUT:VARIABLE'][-1].Variable_Name = 'Zone Thermal Comfort Fanger Model PMV'
        self.idfdevice.idfobjects['OUTPUT:VARIABLE'][-1].Reporting_Frequency = 'Timestep'

        '''Fanger PPD thermal comfort model (Zone Average)'''
        self.idfdevice.newidfobject('OUTPUT:VARIABLE')
        self.idfdevice.idfobjects['OUTPUT:VARIABLE'][-1].Variable_Name = 'Zone Thermal Comfort Fanger Model PPD'
        self.idfdevice.idfobjects['OUTPUT:VARIABLE'][-1].Reporting_Frequency = 'Hourly'

        '''Total Purchase Electric Energy [J]'''
        self.idfdevice.newidfobject('OUTPUT:VARIABLE')
        self.idfdevice.idfobjects['OUTPUT:VARIABLE'][-1].Variable_Name = 'Facility Total Purchased Electric Energy'
        self.idfdevice.idfobjects['OUTPUT:VARIABLE'][-1].Reporting_Frequency = 'Hourly'

        '''Total Zone Internal Heating Energy [J]'''
        self.idfdevice.newidfobject('OUTPUT:VARIABLE')
        self.idfdevice.idfobjects['OUTPUT:VARIABLE'][-1].Variable_Name = 'Zone Total Internal Total Heating Energy'
        self.idfdevice.idfobjects['OUTPUT:VARIABLE'][-1].Reporting_Frequency = 'Hourly'

        '''Total HVAC Demand [W]'''
        self.idfdevice.newidfobject('OUTPUT:VARIABLE')
        self.idfdevice.idfobjects['OUTPUT:VARIABLE'][-1].Variable_Name = 'Facility Total HVAC Electric Demand Power'
        self.idfdevice.idfobjects['OUTPUT:VARIABLE'][-1].Reporting_Frequency = 'Hourly'

        '''Lights Electric Energy [J]'''
        self.idfdevice.newidfobject('OUTPUT:VARIABLE')
        self.idfdevice.idfobjects['OUTPUT:VARIABLE'][-1].Variable_Name = 'Lights Electric Energy'
        self.idfdevice.idfobjects['OUTPUT:VARIABLE'][-1].Reporting_Frequency = 'Hourly'

        '''Electric Equipment Electric Energy [J]'''
        self.idfdevice.newidfobject('OUTPUT:VARIABLE')
        self.idfdevice.idfobjects['OUTPUT:VARIABLE'][-1].Variable_Name = 'Electric Equipment Electric Energy'
        self.idfdevice.idfobjects['OUTPUT:VARIABLE'][-1].Reporting_Frequency = 'Hourly'

        '''Water Heater Heating Energy [J]'''
        self.idfdevice.newidfobject('OUTPUT:VARIABLE')
        self.idfdevice.idfobjects['OUTPUT:VARIABLE'][-1].Variable_Name = 'Water Heater Heating Energy'
        self.idfdevice.idfobjects['OUTPUT:VARIABLE'][-1].Reporting_Frequency = 'Hourly'

        '''Zone Air System Sensible Heating Energy [J]'''
        self.idfdevice.newidfobject('OUTPUT:VARIABLE')
        self.idfdevice.idfobjects['OUTPUT:VARIABLE'][-1].Variable_Name = 'Zone Air System Sensible Heating Energy'
        self.idfdevice.idfobjects['OUTPUT:VARIABLE'][-1].Reporting_Frequency = 'Hourly'

        '''Zone Air System Sensible Cooling Energy [J]'''
        self.idfdevice.newidfobject('OUTPUT:VARIABLE')
        self.idfdevice.idfobjects['OUTPUT:VARIABLE'][-1].Variable_Name = 'Zone Air System Sensible Cooling Energy'
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

        '''Fan Electric Energy [J]'''
        self.idfdevice.newidfobject('OUTPUT:VARIABLE')
        self.idfdevice.idfobjects['OUTPUT:VARIABLE'][-1].Variable_Name = 'Fan Electric Energy'
        self.idfdevice.idfobjects['OUTPUT:VARIABLE'][-1].Reporting_Frequency = 'Hourly'

        '''Cooling Coil Electric Energy [J]'''
        self.idfdevice.newidfobject('OUTPUT:VARIABLE')
        self.idfdevice.idfobjects['OUTPUT:VARIABLE'][-1].Variable_Name = 'Cooling Coil Electric Energy'
        self.idfdevice.idfobjects['OUTPUT:VARIABLE'][-1].Reporting_Frequency = 'Hourly'

        '''Heating Coil Electric Energy [J]'''
        self.idfdevice.newidfobject('OUTPUT:VARIABLE')
        self.idfdevice.idfobjects['OUTPUT:VARIABLE'][-1].Variable_Name = 'Heating Coil Electric Energy'
        self.idfdevice.idfobjects['OUTPUT:VARIABLE'][-1].Reporting_Frequency = 'Hourly'

        '''Heating Coil Gas Energy [J]'''
        self.idfdevice.newidfobject('OUTPUT:VARIABLE')
        self.idfdevice.idfobjects['OUTPUT:VARIABLE'][-1].Variable_Name = 'Heating Coil Gas Energy'
        self.idfdevice.idfobjects['OUTPUT:VARIABLE'][-1].Reporting_Frequency = 'Hourly'

        '''Pump Electric Energy [J]'''
        self.idfdevice.newidfobject('OUTPUT:VARIABLE')
        self.idfdevice.idfobjects['OUTPUT:VARIABLE'][-1].Variable_Name = 'Pump Electric Energy'
        self.idfdevice.idfobjects['OUTPUT:VARIABLE'][-1].Reporting_Frequency = 'Hourly'

        '''Air System Total Cooling Energy [J]'''
        self.idfdevice.newidfobject('OUTPUT:VARIABLE')
        self.idfdevice.idfobjects['OUTPUT:VARIABLE'][-1].Variable_Name = 'Air System Total Cooling Energy'
        self.idfdevice.idfobjects['OUTPUT:VARIABLE'][-1].Reporting_Frequency = 'Hourly'

        '''Air System Total Heating Energy [J]'''
        self.idfdevice.newidfobject('OUTPUT:VARIABLE')
        self.idfdevice.idfobjects['OUTPUT:VARIABLE'][-1].Variable_Name = 'Air System Total Heating Energy'
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
        self.HSP1 = solution.variables[15]
        self.HSP2 = solution.variables[16]
        self.HSP3 = solution.variables[17]
        self.HSP4 = solution.variables[18]
        self.HSP5 = solution.variables[19]
        self.HSP6 = solution.variables[20]
        self.HSP7 = solution.variables[21]
        self.HSP8 = solution.variables[22]
        self.HSP9 = solution.variables[23]
        self.HSP10 = solution.variables[24]
        self.HSP11 = solution.variables[25]
        self.HSP12 = solution.variables[26]
        self.HSP13 = solution.variables[27]
        self.HSP14 = solution.variables[28]
        self.HSP15 = solution.variables[29]
        self.results = buildingSim(self.idfdevice, [self.CSP1, self.CSP2, self.CSP3, self.CSP4, self.CSP5, self.CSP6,
                                                    self.CSP7, self.CSP8, self.CSP9, self.CSP10, self.CSP11, self.CSP12,
                                                    self.CSP13, self.CSP14, self.CSP15], [self.HSP1, self.HSP2,
                                                    self.HSP3, self.HSP4, self.HSP5, self.HSP6, self.HSP7, self.HSP8,
                                                    self.HSP9, self.HSP10, self.HSP11, self.HSP12, self.HSP13,
                                                    self.HSP14, self.HSP15])
        print('=== hvacPower_ave = %f ===' % self.results.hvacPower_ave)
        print('=== allPMV_max = %f ===' % self.results.allPMV_max)
        print('=== allPMV_min = %f ===' % self.results.allPMV_min)

        '''matrix that extracts pmv values for working hours'''
        pmvA = np.identity(48)
        offHours = [0, 1, 2, 3, 4, 5, 18, 19, 20, 21, 22, 23]
        for i in offHours: pmvA[i, i] = 0
        print(pmvA)

        print(pmvA@self.results.allPMV_mean1.T)

        # solution.objectives[:] = [self.results.hvacPower_ave, abs(self.results.allPMV_mean2)]
        solution.objectives[:] = [self.results.hvacPower_ave]
        solution.constraints[:] = [self.results.allPMV_mean2 - 0.5, -(self.results.allPMV_mean2 + 0.5)]

class buildingSim:
    # 'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_19': 'From: %s/%s' % ('1', '10'),
    # 'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_19': 'From: %s/%s' % ('1', '10'),
    def __init__(self, idfdevice, CLG_SETPOINT, HTG_SETPOINT):
        # modify idf with inputs
        self.runJSON = {'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_1': 'Through: %s/%s' % ('12', '31'),
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_2': 'For: Weekday',
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_3': 'Until: 6:00',
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_4': str(CLG_SETPOINT[0]),
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_5': 'Until: 7:00',
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_6': str(CLG_SETPOINT[1]),
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_7': 'Until: 8:00',
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_8': str(CLG_SETPOINT[2]),
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_9': 'Until: 9:00',
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_10': str(CLG_SETPOINT[3]),
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_11': 'Until: 10:00',
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_12': str(CLG_SETPOINT[4]),
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_13': 'Until: 11:00',
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_14': str(CLG_SETPOINT[5]),
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_15': 'Until: 12:00',
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_16': str(CLG_SETPOINT[6]),
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_17': 'Until: 13:00',
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_18': str(CLG_SETPOINT[7]),
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_19': 'Until: 14:00',
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_20': str(CLG_SETPOINT[8]),
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_21': 'Until: 15:00',
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_22': str(CLG_SETPOINT[9]),
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_23': 'Until: 16:00',
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_24': str(CLG_SETPOINT[10]),
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_25': 'Until: 17:00',
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_26': str(CLG_SETPOINT[11]),
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_27': 'Until: 18:00',
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_28': str(CLG_SETPOINT[12]),
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_29': 'Until: 19:00',
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_30': str(CLG_SETPOINT[13]),
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_31': 'Until: 24:00',
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_32': str(CLG_SETPOINT[14]),
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_33': 'For: Weekend',
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_34': 'Until: 24:00',
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_35': str(29.44),
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_36': 'For: Holiday',
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_37': 'Until: 24:00',
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_38': str(29.44),
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_39': 'For: WinterDesignDay',
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_40': 'Until: 24:00',
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_41': str(29.44),
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_42': 'For: SummerDesignDay',
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_43': 'Until: 24:00',
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_44': str(29.44),
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_45': 'For: CustomDay1',
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_46': 'Until: 24:00',
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_47': str(29.44),
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_48': 'For: CustomDay2',
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_49': 'Until: 24:00',
                        'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_50': str(29.44),
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_1': 'Through: %s/%s' % ('12', '31'),
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_2': 'For: Weekday',
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_3': 'Until: 6:00',
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_4': str(HTG_SETPOINT[0]),
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_5': 'Until: 7:00',
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_6': str(HTG_SETPOINT[1]),
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_7': 'Until: 8:00',
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_8': str(HTG_SETPOINT[2]),
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_9': 'Until: 9:00',
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_10': str(HTG_SETPOINT[3]),
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_11': 'Until: 10:00',
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_12': str(HTG_SETPOINT[4]),
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_13': 'Until: 11:00',
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_14': str(HTG_SETPOINT[5]),
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_15': 'Until: 12:00',
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_16': str(HTG_SETPOINT[6]),
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_17': 'Until: 13:00',
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_18': str(HTG_SETPOINT[7]),
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_19': 'Until: 14:00',
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_20': str(HTG_SETPOINT[8]),
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_21': 'Until: 15:00',
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_22': str(HTG_SETPOINT[9]),
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_23': 'Until: 16:00',
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_24': str(HTG_SETPOINT[10]),
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_25': 'Until: 17:00',
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_26': str(HTG_SETPOINT[11]),
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_27': 'Until: 18:00',
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_28': str(HTG_SETPOINT[12]),
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_29': 'Until: 19:00',
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_30': str(HTG_SETPOINT[13]),
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_31': 'Until: 24:00',
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_32': str(HTG_SETPOINT[14]),
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_33': 'For: Weekend',
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_34': 'Until: 24:00',
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_35': str(29.44),
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_36': 'For: Holiday',
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_37': 'Until: 24:00',
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_38': str(29.44),
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_39': 'For: WinterDesignDay',
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_40': 'Until: 24:00',
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_41': str(29.44),
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_42': 'For: SummerDesignDay',
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_43': 'Until: 24:00',
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_44': str(29.44),
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_45': 'For: CustomDay1',
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_46': 'Until: 24:00',
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_47': str(29.44),
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_48': 'For: CustomDay2',
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_49': 'Until: 24:00',
                        'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_50': str(29.44)
                        }



        # self.runJSON = {'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_1': 'Through: 12/31',
        #            'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_2': 'For: Weekday',
        #            'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_3': 'Until: 6:00',
        #            'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_4': str(HTG_SETPOINT[0]),
        #            'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_5': 'Until: 7:00',
        #            'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_6': str(HTG_SETPOINT[1]),
        #            'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_7': 'Until: 8:00',
        #            'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_8': str(HTG_SETPOINT[2]),
        #            'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_9': 'Until: 19:00',
        #            'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_10': str(HTG_SETPOINT[3]),
        #            'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_11': 'Until: 24:00',
        #            'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_12': str(HTG_SETPOINT[4]),
        #            'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_13': 'For: Weekend',
        #            'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_14': 'Until: 24:00',
        #            'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_15': str(HTG_SETPOINT[5]),
        #            'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_16': 'For: Holiday',
        #            'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_17': 'Until: 24:00',
        #            'idf.SCHEDULE:COMPACT.HTGSETP_SCH_YES_OPTIMUM.Field_18': str(HTG_SETPOINT[6]),
        #            'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_1': 'Through: 12/31',
        #            'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_2': 'For: Weekday',
        #            'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_3': 'Until: 6:00',
        #            'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_4': str(CLG_SETPOINT[0]),
        #            'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_5': 'Until: 7:00',
        #            'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_6': str(CLG_SETPOINT[1]),
        #            'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_7': 'Until: 8:00',
        #            'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_8': str(CLG_SETPOINT[2]),
        #            'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_9': 'Until: 19:00',
        #            'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_10': str(CLG_SETPOINT[3]),
        #            'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_11': 'Until: 24:00',
        #            'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_12': str(CLG_SETPOINT[4]),
        #            'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_13': 'For: Weekend',
        #            'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_14': 'Until: 24:00',
        #            'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_15': str(CLG_SETPOINT[5]),
        #            'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_16': 'For: Holiday',
        #            'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_17': 'Until: 24:00',
        #            'idf.SCHEDULE:COMPACT.CLGSETP_SCH_YES_OPTIMUM.Field_18': str(CLG_SETPOINT[6])}

        json_functions.updateidf(idfdevice, self.runJSON)

        # run IDF and the associated batch file to export the custom csv output
        # self, idf='SmallOffice.idf', weather='USA_UT_Salt.Lake.City.Intl.AP.725720_TMY3.epw', ep_version='8-5-0'
        idfdevice.run(verbose='q')
        os.system(r'CD E:\Masters Thesis\EnergyPlus MPC\Simulations\Baseline')
        os.system('CustomCSV SO OUTPUT')

        # self.smallofficeoutputs('SO_OUTPUT_hourly.csv')

        # Read csv file into new data dictionary
        newEntry = defaultdict(list)
        with open('SO_OUTPUT_hourly.csv', newline='') as newFile:
            newData = csv.DictReader(newFile)
            for row in newData:
                [newEntry[key].append(value) for key, value in row.items()]

        '''Date/Time array'''
        self.DateTime = np.asarray(newEntry['Date/Time'], dtype=str)

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










