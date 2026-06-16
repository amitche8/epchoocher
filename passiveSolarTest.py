import eppy
from eppy.modeleditor import IDF
import os
import shutil
import itertools
from multiprocessing import Pool, cpu_count, freeze_support
import multiprocessing
import json
import time
import pandas as pd
import random


time1 = time.time()
# EP Choocher Paths
# EP_PATH = r"/usr/local/EnergyPlus-25-1-0"
# base_idf_path = r"/home/amitche8/PassiveSolarBase.idf"
# epw_path = r"/home/amitche8/epwFiles/USA_IL_Chicago-Midway.AP.725340_TMY3.epw"
# study_dir = r"/home/amitche8/PassiveSolarTest"

# Thinkpad Paths
EP_PATH = r"C:\EnergyPlusV25-1-0"
base_idf_path = r"C:\Users\amitc_crl\OneDrive\Documents\GitHub\epchoocher\idfFiles\PassiveSolarBase.idf"
epw_path = r"C:\Users\amitc_crl\OneDrive\Documents\GitHub\epchoocher\epwFiles\USA_IL_Chicago-Midway.AP.725340_TMY3.epw"
study_dir = r"C:\Users\amitc_crl\OneDrive\Documents\GitHub\epchoocher\PassiveSolarTest"

# Set up the E+ Environment
iddfile = os.path.join(EP_PATH, 'Energy+.idd')
IDF.setiddname(iddfile)

# Create the various parameter values to test
# For some of the decimal variables, it is only possible to generate integer values and multiply them into decimals
# Larger switches can be done with if statements later in the code, ie swapping mechanical systems
shade_pf = list(round(x * 0.01, 2) for x in range(5, 105, 5))
north_axis_values = list(range(-30, 30, 5))
shgc_values = list(round(x*0.01, 2) for x in range(20, 60, 5))
u_values = list(round(x*0.01, 2) for x in range(50, 300, 25))

# Create results and final idf directories, removing any old ones if they exist later in the code
results_dir = os.path.join(study_dir, "temp results")
final_idf_dir = os.path.join(study_dir, "final idfs")

# Everthing in this function is run for each case, and it needs to live in this function to be run in parallel with multiprocessing
def run_passive_solar_test(north_axis, 
                           projection_factor, shgc, u_factor):
    
    # Create a unique idenifier for each case, and can be used for file naming
    case_number = f"NA{north_axis}_PF{projection_factor}_SHGC{shgc}_U{u_factor}"

    # set up the idf
    idf1 = IDF(base_idf_path,epw=epw_path)

    idf1.idfobjects["building"][0].North_Axis = north_axis

    idf1.idfobjects["Shading:Overhang:Projection"][0].Depth_as_Fraction_of_WindowDoor_Height = projection_factor

    idf1.idfobjects["WindowMaterial:SimpleGlazingSystem"][0].Solar_Heat_Gain_Coefficient = shgc
    idf1.idfobjects["WindowMaterial:SimpleGlazingSystem"][0].UFactor = u_factor

    # Make temp director for the case to run the simulation in
    temp_dir = os.path.join(study_dir, f"temp {case_number}")
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir, ignore_errors=True)
    os.makedirs(temp_dir, exist_ok=True)

    old_cwd = os.getcwd()
    try:
        os.chdir(temp_dir)
        
        # Save the version in the temp directory to run
        idf1.saveas(os.path.join(temp_dir, f"PassiveSolarTest{case_number}.idf"))

        # Save the final version to be re-run later, or to make the optimal case from
        idf1.saveas(os.path.join(final_idf_dir, f"PassiveSolarTest{case_number}.idf"))

        # Run E+
        idf2 = IDF(os.path.join(temp_dir, f"PassiveSolarTest{case_number}.idf"), epw=epw_path)
        idf2.run()

        # Read results from the .json results file - this is far faster than reading from the html tables
        results_json = os.path.join(temp_dir, "eplusout.json")
        if os.path.exists(results_json):    
            with open(results_json) as f:
                results = json.load(f)

            try:
                cooling = float(results["TabularReports"][0]["Tables"][1]["Rows"]["Cooling"][10])
                heating = float(results["TabularReports"][0]["Tables"][1]["Rows"]["Heating"][11])
            except (KeyError, ValueError):
                cooling = "error"
                heating = "error"

            case_result = {
                "north_axis": north_axis,
                "projection_factor": projection_factor,
                "shgc": shgc,
                "u_factor": u_factor,
                "cooling": cooling,
                "heating": heating,
            }

            json_path = os.path.join(results_dir, f"case_{case_number}.json")
            with open(json_path, "w") as f:
                json.dump(case_result, f, indent=4)

            return case_number, case_result

        return case_number, None
    finally:
        os.chdir(old_cwd)
        shutil.rmtree(temp_dir, ignore_errors=True)

# multiprocessing happens here
if __name__ == '__main__':
    multiprocessing.freeze_support()
    os.chdir(study_dir)

    # make final directories, remove existing if present
    if os.path.exists(results_dir):
        shutil.rmtree(results_dir, ignore_errors=True)
    os.makedirs(results_dir, exist_ok=True)

    if os.path.exists(final_idf_dir):
        shutil.rmtree(final_idf_dir, ignore_errors=True)
    os.makedirs(final_idf_dir, exist_ok=True)

    # make all possible variations
    total_cases = list(itertools.product(north_axis_values, 
                                   shade_pf, shgc_values, u_values))
    
    # cases = total_cases

    # sample of cases
    cases = random.sample(total_cases,4)

    print(f"Running {len(cases)} cases on {cpu_count()} CPU cores...")

    with Pool(processes=cpu_count()) as pool:
        results = pool.starmap(run_passive_solar_test, cases)

    summary = {case: data for case, data in results if data is not None}
    if summary:
        pd.DataFrame.from_dict(summary, orient="index").to_csv(os.path.join(results_dir, "results.csv"), index_label="Case")
    else:
        print("No case results were generated.")

    time2 = time.time()
    print(f"Time taken: {round(time2 - time1, 2)} seconds")