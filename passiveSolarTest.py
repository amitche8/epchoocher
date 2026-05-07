import eppy
from eppy.modeleditor import IDF
import os
import itertools


EP_PATH = r"C:\EnergyPlusV25-1-0"
iddfile = os.path.join(EP_PATH, 'Energy+.idd')
IDF.setiddname(iddfile)

base_idf_path = r"C:\Users\michael\Documents\GitHub\PassiveSolarTest\base.idf"

def run_passive_solar_test():
