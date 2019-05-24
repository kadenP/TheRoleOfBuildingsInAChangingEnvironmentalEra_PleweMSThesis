'''
Kaden Plewe
03/12/2019
Script used to generate a database of building model inputs used for training regression models from energy plus
simulations.
This script will take in an idf file as an input and will generate a .txt file containing the idf parameters and
relevant information for identifying the parameters in the building model in json format.
'''

'''import libraries'''
from SmallOfficeModules import configuresmalloffice
import eppy
from eppy.modeleditor import IDF
import numpy as np
import random
import json
import math
import eppy.json_functions as json_functions

'''user defined functions'''
def constrain(n, minn=-math.inf, maxn=math.inf):
    return max(min(maxn, n), minn)

'''define the .idf file parameters'''
iddfile = "C:\EnergyPlusV8-5-0\Energy+.idd"
fname = "SmallOffice.idf"
weatherfile = "USA_MI_Lansing-Capital.City.AP.725390_TMY3.epw"

'''dictionary that will contain relevent parameters'''
paramSet = {}
paramSet['input'] = []
paramSet['all fields'] = []

'''initialize the .idf file for eppy usage'''
IDF.setiddname(iddfile)
idfdevice = IDF(fname, weatherfile)

'''sample space parameter definitions for sensitivity analysis'''
N = 10000   # number of randomly sampled values for each parameter
uncertainty = 20
X = uncertainty      # uncertainty interval percentage

'''declare the classes that will be considered when parsing the idf file'''

'''ALL Classes'''
objectClassList = ['SCHEDULE:COMPACT', 'SETPOINTMANAGER:SINGLEZONE:REHEAT', 'PEOPLE',
                   'WINDOWMATERIAL:GLAZING', 'MATERIAL', 'MATERIAL:NOMASS', 'WINDOWMATERIAL:GAS',
                   'LIGHTS', 'PLANTLOOP', 'AVAILABILITYMANAGER:NIGHTCYCLE', 'WATERUSE:EQUIPMENT', 'ELECTRICEQUIPMENT',
                   'EXTERIOR:LIGHTS', 'DESIGNSPECIFICATION:OUTDOORAIR', 'WATERHEATER:MIXED', 'FAN:ONOFF',
                   'COIL:COOLING:DX:SINGLESPEED', 'COIL:HEATING:DX:SINGLESPEED', 'COIL:HEATING:GAS',
                   'CONTROLLER:OUTDOORAIR', 'AIRLOOPHVAC:UNITARYHEATPUMP:AIRTOAIR', 'PUMP:CONSTANTSPEED']

'''Set One (SCHEDULES/SETPOINTS) added PEOPLE because it's coupled closely with scheduling'''
# objectClassList = ['SCHEDULE:COMPACT', 'SETPOINTMANAGER:SINGLEZONE:REHEAT', 'PEOPLE']
#
'''Set Two (MATERIALS)'''
# objectClassList = ['WINDOWMATERIAL:GLAZING', 'MATERIAL', 'MATERIAL:NOMASS', 'WINDOWMATERIAL:GAS']

'''Set Three (EQUIPMENT)'''
# objectClassList = ['LIGHTS', 'PLANTLOOP', 'AVAILABILITYMANAGER:NIGHTCYCLE', 'WATERUSE:EQUIPMENT', 'ELECTRICEQUIPMENT', 'EXTERIOR:LIGHTS', 'DESIGNSPECIFICATION:OUTDOORAIR',
#                    'WATERHEATER:MIXED', 'FAN:ONOFF', 'COIL:COOLING:DX:SINGLESPEED', 'COIL:HEATING:DX:SINGLESPEED', 'COIL:HEATING:GAS',
#                    'CONTROLLER:OUTDOORAIR', 'AIRLOOPHVAC:UNITARYHEATPUMP:AIRTOAIR', 'PUMP:CONSTANTSPEED']
#
    # #, 'ZONEINFILTRATION:DESIGNFLOWRATE', 'SIZING:PARAMETERS', 'SIZING:ZONE'
    #
# ,
#
# 'ZONEINFILTRATION:DESIGNFLOWRATE'

#(Neglected) 'BUILDING', 'SHADOWCALCULATION', 'SITE:WATERMAINSTEMPERATURE', 'DAYLIGHTING:CONTROLS', 'CURVE:QUADRATIC', 'CURVE:BIQUADRATIC', 'CURVE:CUBIC'
'''
!-                                ===========  ALL OBJECTS IN CLASS: X ===========
!- handling/transfering of all objects and fields in the selected classes into a sorted dictionary that contains both
!- a set of all the fields in the classes of interest ('all fields') and all of the fields that will be manipulated in
!- the sensitivity analysis.
'''
print('================== Extracting IDF Groups ==================')
for objectClass in objectClassList:
    for object in idfdevice.idfobjects[objectClass]:
        # print(object.name)
        # print(object.fieldnames)
        for fieldname in object.fieldnames:
            try:
                objectName = object.Name
                # print(fieldname)
                # print(objectName)
                eppyJSON = 'idf.' + objectClass + '.' + objectName + '.' + fieldname
            except:
                if objectClass == 'SIZING:ZONE':
                    objectName = object.Zone_or_ZoneList_Name
                    eppyJSON = 'idf.' + objectClass + '.' + objectName + '.' + fieldname
                else:
                    objectName = 'UNDECLARED'
                    eppyJSON = 'idf.' + objectClass + '.' + '.' + fieldname
            try:
                object[fieldname] = float(object[fieldname])
            except ValueError:
                object[fieldname] = object[fieldname]

            '''set flag to not change parameter if discrete'''
            try:
                if any([object.Schedule_Type_Limits_Name == 'On/Off', object.Schedule_Type_Limits_Name == 'ON/OFF',
                        object.Schedule_Type_Limits_Name == 'on/off', object.Schedule_Type_Limits_Name == 'Control Type']):
                    passParam = 1
                else:
                    passParam = 0
            except:
                passParam = 0
            if any( [type(object[fieldname]).__name__ == 'int', type(object[fieldname]).__name__ == 'float']) and \
                    all(['Maximum' not in fieldname, 'Minimum' not in fieldname, passParam == 0]):

                '''reduce the uncertainty interval for temperature set points'''
                try:
                    if object.Schedule_Type_Limits_Name == 'Temperature':
                        print('test')
                        print('Setpoint Uncertainty neglected for %s' % object.Name)
                        X = 0.05
                except:
                    pass

                '''generate scaled nominal value (1.3 unless nominal value is zero'''
                nomValNorm = 0 if object[fieldname] == 0 else 1/1.3

                '''generate sample space of parameters that can be used for a sensitivity analysis'''
                objectRange = object.getrange(fieldname)
                nomVal = object[fieldname]
                uncertaintyInt = X / 100.0 * nomVal

                '''set the acceptable range of the current parameter'''
                if objectRange['maximum'] != None or objectRange['minimum'] != None \
                        or objectRange['maximum<'] != None or objectRange['minimum>'] != None:
                    '''extract the range of the current parameter'''
                    if objectRange['maximum<'] == None and objectRange['minimum>'] == None:
                        paramRange = [objectRange['minimum'], objectRange['maximum']]
                    elif objectRange['maximum<'] != None and objectRange['minimum>'] == None:
                        paramRange = [objectRange['minimum'], objectRange['maximum<']-1e-8]
                    elif objectRange['maximum<'] == None and objectRange['minimum>'] != None:
                        paramRange = [objectRange['minimum>']+1e-8, objectRange['maximum']]
                    else:
                        paramRange = [objectRange['minimum>']+1e-8, objectRange['maximum<']-1e-8]

                    '''convert range max and min to float scalars'''
                    for i in range(len(paramRange)):
                        if paramRange[i] == None and i == 0:
                            paramRange[i] = -math.inf
                        elif paramRange[i] == None and i == 1:
                            paramRange[i] = math.inf
                        else:
                            paramRange[i] = float(paramRange[i][0]) if type(paramRange[i]) is list else paramRange[i]
                elif objectClass == 'SCHEDULE:COMPACT' and object.Schedule_Type_Limits_Name == 'fraction':
                    paramRange = [0, 1]
                elif objectClass == 'SCHEDULE:COMPACT' and object.Schedule_Type_Limits_Name == 'Fraction':
                    paramRange = [0, 1]
                elif objectClass == 'SCHEDULE:COMPACT' and object.Schedule_Type_Limits_Name == 'FRACTION':
                    paramRange = [0, 1]
                elif objectClass == 'SCHEDULE:COMPACT' and object.Schedule_Type_Limits_Name == 'CONTROL TYPE':
                    paramRange = [0, 4]
                else: paramRange = [-math.inf, math.inf]


                '''append constrained value to the Sampling Parameter set'''
                if objectClass == 'LIGHTS' and fieldname == 'Fraction_Radiant':
                    print('=== Fraction Radiant in %s %s Constrained Uniquely ==='%(objectClass, object.Name))
                    fracRadiant = np.ones(N); fracVisible = np.ones(N)
                    nomVal1 = object['Fraction_Visible']
                    uncertaintyInt1 = X / 100.0 * nomVal1
                    N_found = 0; N_need = N
                    while N_found < N:
                        findFracRadiant = np.clip(np.random.uniform(nomVal - uncertaintyInt, nomVal + uncertaintyInt, N), 1e-8, 1 - 1e-8)
                        findFracVisible = np.clip(np.random.uniform(nomVal1 - uncertaintyInt1, nomVal1 + uncertaintyInt1, N), 1e-8, 1 - 1e-8)
                        ind = np.logical_and(findFracRadiant + findFracVisible < 1, findFracRadiant + findFracVisible < 1).nonzero()[0]
                        if len(ind) != 0:
                            if len(ind) > N_need:
                                ind = ind[0:N_need]
                            fracRadiant[N_found:N_found + len(ind)] = findFracRadiant[ind]
                            fracVisible[N_found:N_found + len(ind)] = findFracVisible[ind]
                            N_found = N_found + len(ind)
                            N_need = N - N_found
                    paramSamples = fracRadiant
                elif objectClass == 'LIGHTS' and fieldname == 'Fraction_Visible':
                    print('=== Fraction Visible in %s %s Constrained Uniquely ==='%(objectClass, object.Name))
                    paramSamples = fracVisible
                elif objectClass == 'LIGHTS' and fieldname == 'Return_Air_Fraction':
                    print('=== Return Air Fraction in %s %s Constrained Uniquely ==='%(objectClass, object.Name))
                    fracRA = np.ones(N); fracReplaceable = np.ones(N)
                    nomVal1 = object['Fraction_Replaceable']
                    uncertaintyInt1 = X / 100.0 * nomVal1
                    N_found = 0; N_need = N
                    while N_found < N:
                        findFracRA = np.clip(np.random.uniform(nomVal - uncertaintyInt, nomVal + uncertaintyInt, N), 1e-8, 1 - 1e-8)
                        findFracReplaceable = np.clip(np.random.uniform(nomVal1 - uncertaintyInt1, nomVal1 + uncertaintyInt1, N), 1e-8, 1 - 1e-8)
                        ind = np.logical_and(findFracRA + findFracReplaceable < 1, findFracRA + findFracReplaceable < 1).nonzero()[0]
                        if len(ind) != 0:
                            if len(ind) > N_need:
                                ind = ind[0:N_need]
                            fracRA[N_found:N_found + len(ind)] = findFracRA[ind]
                            fracReplaceable[N_found:N_found + len(ind)] = findFracReplaceable[ind]
                            N_found = N_found + len(ind)
                            N_need = N - N_found
                    paramSamples = fracRA
                elif objectClass == 'LIGHTS' and fieldname == 'Fraction_Replaceable':
                    print('=== Fraction Replaceable in %s %s Constrained Uniquely ==='%(objectClass, object.Name))
                    paramSamples = fracReplaceable
                elif objectClass == 'WINDOWMATERIAL:GLAZING' and fieldname == 'Solar_Transmittance_at_Normal_Incidence':
                    print('=== Solar Transmittance at Normal Incidence in %s %s Constrained Uniquely ===' % (objectClass, object.Name))
                    solarTransmittance = np.ones(N); frontSolarReflectance = np.ones(N); backSolarReflectance = np.ones(N)
                    nomVal1 = object['Front_Side_Solar_Reflectance_at_Normal_Incidence']
                    uncertaintyInt1 = X / 100.0 * nomVal1
                    nomVal2 = object['Back_Side_Solar_Reflectance_at_Normal_Incidence']
                    uncertaintyInt2 = X / 100.0 * nomVal2
                    N_found = 0; N_need = N
                    while N_found < N:
                        findSolarTransmittance = np.clip(np.random.uniform(nomVal - uncertaintyInt, nomVal + uncertaintyInt, N), 1e-8, 1 - 1e-8)
                        findFrontSolarReflectance = np.clip(np.random.uniform(nomVal1 - uncertaintyInt1, nomVal1 + uncertaintyInt1, N), 1e-8, 1 - 1e-8)
                        findBackSolarReflectance = np.clip(np.random.uniform(nomVal2 - uncertaintyInt2, nomVal2 + uncertaintyInt2, N), 1e-8, 1 - 1e-8)
                        ind = np.logical_and(findSolarTransmittance + findFrontSolarReflectance < 1,
                                   findSolarTransmittance + findBackSolarReflectance < 1).nonzero()[0]
                        if len(ind) != 0:
                            if len(ind) > N_need:
                                ind = ind[0:N_need]
                            solarTransmittance[N_found:N_found + len(ind)] = findSolarTransmittance[ind]
                            frontSolarReflectance[N_found:N_found + len(ind)] = findFrontSolarReflectance[ind]
                            backSolarReflectance[N_found:N_found + len(ind)] = findBackSolarReflectance[ind]
                            N_found = N_found + len(ind)
                            N_need = N - N_found
                    paramSamples = solarTransmittance
                elif objectClass == 'WINDOWMATERIAL:GLAZING' and fieldname == 'Front_Side_Solar_Reflectance_at_Normal_Incidence':
                    print('=== Front Solar Reflectance at Normal Incidence in %s %s Constrained Uniquely ===' % (objectClass, object.Name))
                    paramSamples = frontSolarReflectance
                elif objectClass == 'WINDOWMATERIAL:GLAZING' and fieldname == 'Back_Side_Solar_Reflectance_at_Normal_Incidence':
                    print('=== Back Solar Reflectance at Normal Incidence in %s %s Constrained Uniquely ===' % (objectClass, object.Name))
                    paramSamples = backSolarReflectance
                elif objectClass == 'WINDOWMATERIAL:GLAZING' and fieldname == 'Visible_Transmittance_at_Normal_Incidence':
                    print('=== Visible Transmittance at Normal Incidence in %s %s Constrained Uniquely ===' % (objectClass, object.Name))
                    visibleTransmittance = np.ones(N); frontVisibleReflectance = np.ones(N); backVisibleReflectance = np.ones(N)
                    nomVal1 = object['Front_Side_Visible_Reflectance_at_Normal_Incidence']
                    uncertaintyInt1 = X / 100.0 * nomVal1
                    nomVal2 = object['Back_Side_Visible_Reflectance_at_Normal_Incidence']
                    uncertaintyInt2 = X / 100.0 * nomVal2
                    N_found = 0; N_need = N
                    while N_found < N:
                        findVisibleTransmittance = np.clip(np.random.uniform(nomVal - uncertaintyInt, nomVal + uncertaintyInt, N), 1e-8, 1 - 1e-8)
                        findFrontVisibleReflectance = np.clip(np.random.uniform(nomVal1 - uncertaintyInt1, nomVal1 + uncertaintyInt1, N), 1e-8, 1 - 1e-8)
                        findBackVisibleReflectance = np.clip(np.random.uniform(nomVal2 - uncertaintyInt2, nomVal2 + uncertaintyInt2, N), 1e-8, 1 - 1e-8)
                        ind = np.logical_and(findVisibleTransmittance + findFrontVisibleReflectance < 1,
                                   findVisibleTransmittance + findBackVisibleReflectance < 1).nonzero()[0]
                        if len(ind) != 0:
                            if len(ind) > N_need:
                                ind = ind[0:N_need]
                            visibleTransmittance[N_found:N_found + len(ind)] = findVisibleTransmittance[ind]
                            frontVisibleReflectance[N_found:N_found + len(ind)] = findFrontVisibleReflectance[ind]
                            backVisibleReflectance[N_found:N_found + len(ind)] = findBackVisibleReflectance[ind]
                            N_found = N_found + len(ind)
                            N_need = N - N_found
                    paramSamples = visibleTransmittance
                elif objectClass == 'WINDOWMATERIAL:GLAZING' and fieldname == 'Front_Side_Visible_Reflectance_at_Normal_Incidence':
                    print('=== Front Side Visible Reflectance at Normal Incidence in %s %s Constrained Uniquely ===' % (objectClass, object.Name))
                    paramSamples = frontVisibleReflectance
                elif objectClass == 'WINDOWMATERIAL:GLAZING' and fieldname == 'Back_Side_Visible_Reflectance_at_Normal_Incidence':
                    print('=== Back Side Visible Reflectance at Normal Incidence in %s %s Constrained Uniquely ===' % (objectClass, object.Name))
                    paramSamples = backVisibleReflectance
                elif objectClass == 'WINDOWMATERIAL:GLAZING' and fieldname == 'Infrared_Transmittance_at_Normal_Incidence':
                    print('=== Infrared Transmittance at Normal Incidence in %s %s Constrained Uniquely ===' % (objectClass, object.Name))
                    infraredTransmittance = np.ones(N); frontInfraredEmissivity = np.ones(N); backInfraredEmissivity = np.ones(N)
                    nomVal1 = object['Front_Side_Infrared_Hemispherical_Emissivity']
                    uncertaintyInt1 = X / 100.0 * nomVal1
                    nomVal2 = object['Back_Side_Infrared_Hemispherical_Emissivity']
                    uncertaintyInt2 = X / 100.0 * nomVal2
                    N_found = 0; N_need = N
                    while N_found < N:
                        findInfraredTransmittance = np.clip(np.random.uniform(nomVal - uncertaintyInt, nomVal + uncertaintyInt, N), 1e-8, 1 - 1e-8)
                        findFrontInfraredEmissivity = np.clip(np.random.uniform(nomVal1 - uncertaintyInt1, nomVal1 + uncertaintyInt1, N), 1e-8, 1 - 1e-8)
                        findBackInfraredEmissivity = np.clip(np.random.uniform(nomVal2 - uncertaintyInt2, nomVal2 + uncertaintyInt2, N), 1e-8, 1 - 1e-8)
                        ind = np.logical_and(findInfraredTransmittance + findFrontInfraredEmissivity < 1,
                                   findInfraredTransmittance + findBackInfraredEmissivity < 1).nonzero()[0]
                        if len(ind) != 0:
                            if len(ind) > N_need:
                                ind = ind[0:N_need]
                            infraredTransmittance[N_found:N_found + len(ind)] = findInfraredTransmittance[ind]
                            frontInfraredEmissivity[N_found:N_found + len(ind)] = findFrontInfraredEmissivity[ind]
                            backInfraredEmissivity[N_found:N_found + len(ind)] = findBackInfraredEmissivity[ind]
                            N_found = N_found + len(ind)
                            N_need = N - N_found
                    paramSamples = infraredTransmittance
                elif objectClass == 'WINDOWMATERIAL:GLAZING' and fieldname == 'Front_Side_Infrared_Hemispherical_Emissivity':
                    print('=== Front Side Infrared Hemispherical Emissivity in %s %s Constrained Uniquely' % (objectClass, object.Name))
                    paramSamples = frontInfraredEmissivity
                elif objectClass == 'WINDOWMATERIAL:GLAZING' and fieldname == 'Back_Side_Infrared_Hemispherical_Emissivity':
                    print('=== Back Side Infrared Hemispherical Emissivity in %s %s Constrained Uniquely' % (objectClass, object.Name))
                    paramSamples = backInfraredEmissivity
                elif nomVal != 0:
                    paramSamples = np.clip(np.random.uniform(nomVal - uncertaintyInt, nomVal + uncertaintyInt, N),
                                                  paramRange[0], paramRange[1])
                else:
                    paramSamples = np.random.triangular(0, 0, 0.1 * paramRange[1], N) if paramRange[1] != math.inf else \
                        np.random.triangular(0, 0, 0.1, N)
                try:
                    paramSamplesNorm = np.clip(np.random.uniform(nomVal - uncertaintyInt, nomVal + uncertaintyInt, N),
                                              paramRange[0], paramRange[1])*(1/constrain(nomVal*(1 + 30/100), nomVal, paramRange[1]))
                except ZeroDivisionError:
                    paramSamplesNorm = np.random.triangular(0, 0, 0.3 * paramRange[1], N) if paramRange[1] != math.inf else \
                        np.random.triangular(0, 0, 0.1, N)


                paramSet['input'].append({'ID': len(paramSet['input']),
                                          'Object Name': objectName,
                                          'Field Name': fieldname,
                                          'Nominal Value': object[fieldname],
                                          'Scaled Nominal Value': nomValNorm,
                                          'eppy json string': eppyJSON,
                                          'Sample Values': np.ndarray.tolist(paramSamples),
                                          'Scaled Values': np.ndarray.tolist(paramSamplesNorm),
                                          'Range': object.getrange(fieldname)})

                X = uncertainty

            # paramSet['all fields'].append({'ID': len(paramSet['all fields']),
            #                                'Object Name': objectName,
            #                                'Field Name': fieldname,
            #                                'Nominal Value': object[fieldname],
            #                                'Range': object.getrange(fieldname)})
'''download the new dictionary into a json text file'''
filename = 'jsonOUTPUT_ALL_Test.txt'
with open(filename, 'w') as outfile:
    json.dump(paramSet, outfile)
print('%.0f numerical parameters were found and downloaded to %s' % (len(paramSet['input']), filename))


'''--------------------------------------------------------------------------------------------------------
Test Data Ranges
--------------------------------------------------------------------------------------------------------'''
'''JSON parameters'''
with open('jsonOUTPUT_ALL_Test.txt') as jsonParams:
    paramSet = json.load(jsonParams)

'''files used for energy plus simulation'''
iddfile = "C:\EnergyPlusV8-5-0\Energy+.idd"
fname = "SmallOffice.idf"
weatherfile = "USA_UT_Salt.Lake.City.Intl.AP.725720_TMY3.epw"

'''initialize idf file'''
IDF.setiddname(iddfile)
idfdevice = IDF(fname, weatherfile)

'''declare simulation run period'''
Begin_Month = '1'
Begin_Day_of_Month = '14'
End_Month = '1'
End_Day_of_Month = '24'

'''configure the idf file that will be used for simulations'''
configuresmalloffice(idfdevice, Begin_Month, Begin_Day_of_Month, End_Month, End_Day_of_Month)

'''run parametric simulations'''
for i in range(N):
    # for i in range(50):
    '''update JSON file and input parameter array for training meta model'''
    runJSON = {}

    for obj in paramSet['input']:
        runJSON[obj['eppy json string']] = obj['Sample Values'][i]

    json_functions.updateidf(idfdevice, runJSON)

    '''run IDF and the associated batch file to export the custom csv output'''
    idfdevice.run(verbose='q')





