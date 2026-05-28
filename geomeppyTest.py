# import eppy
# from eppy.modeleditor import IDF

import geomeppy
from geomeppy import IDF
import os
import itertools

os.chdir(r"C:\Users\amitc_crl\OneDrive\Documents\GitHub\epchoocher\idfFiles")


EP_PATH = r"C:\EnergyPlusV25-1-0"
baseIDFpath = r"C:\EnergyPlusV25-1-0\ExampleFiles\Minimal.idf"
epwPath = r"C:\Users\amitc_crl\OneDrive\Documents\GitHub\epchoocher\epwFiles\USA_IL_Chicago-Midway.AP.725340_TMY3.epw"

iddfile = os.path.join(EP_PATH, 'Energy+.idd')
IDF.setiddname(iddfile)


idf1 = IDF(baseIDFpath)
idf1.epw = epwPath

idf1.add_block(
    name='Two storey',
    coordinates=[(10,0),(10,5),(0,5),(0,0)],
    height=6,
    num_stories=2,
    )

idf1.add_block(
    name='One storey',
    coordinates=[(10,5),(10,10),(0,10),(0,5)],
    height=3,
    )

stat = idf1.newidfobject(
      "HVACTEMPLATE:THERMOSTAT",
      Name="Zone Stat",
      Constant_Heating_Setpoint=20,
      Constant_Cooling_Setpoint=25,
    )

for zone in idf1.idfobjects["ZONE"]:
      idf1.newidfobject(
          "HVACTEMPLATE:ZONE:IDEALLOADSAIRSYSTEM",
          Zone_Name=zone.Name,
          Template_Thermostat_Name=stat.Name,
    )


idf1.newidfobject(
        "OUTPUT:VARIABLE",
        Variable_Name="Zone Ideal Loads Supply Air Total Heating Energy",
        Reporting_Frequency="Hourly",
    )

idf1.newidfobject(
        "OUTPUT:VARIABLE",
        Variable_Name="Zone Ideal Loads Supply Air Total Cooling Energy",
        Reporting_Frequency="Hourly",
    )

idf1.intersect_match()

# idf1.set_wwr(wwr=0, wwr_map={180: 0.3})
idf1.set_wwr(wwr_map={0:0.1, 90:0.1, 180: 0.6, 270:0.1})
# idf.set_wwr(south, construction="Project External Window", orientation="south")

for window in idf1.idfobjects["FENESTRATIONSURFACE:DETAILED"]:
    windowName = window.Name

    idf1.newidfobject("SHADING:OVERHANG:PROJECTION", 
                      Name=f"{windowName} overhang", 
                      Window_or_Door_Name = windowName, 
                      Depth_as_Fraction_of_WindowDoor_Height=0.5)


idf1.set_default_constructions()

# idf1.to_obj('idf1.obj')

# IDF.view_model(idf1)

idf1.run()

idf1.saveas('idf1.idf')