from typing import Tuple
from prefect import task, Flow, unmapped
from prefect.engine.executors import LocalDaskExecutor, DaskExecutor
import PySAM.Pvsamv1 as pv
import numpy as np
import itertools
import json


def script_path(filename):
    """
    A convenience function to get the absolute path to a file in this
    tutorial's directory. This allows the tutorial to be launched from any
    directory.
    """
    import os

    filepath = os.path.join(os.path.dirname(__file__))
    return os.path.join(filepath, filename)


@task
def load_profile(filename="data/Max_load_profile_for_year.txt"):
    return np.loadtxt(filename, skiprows=1)


@task(nout=True)
def generate_modules_X_strings(modules=range(2, 8), strings=range(4, 15)):

    modules_X_strings = list(itertools.product(modules, strings))
    return modules_X_strings


@task
def execute_pvmodel(input, our_load_profile, inverters=4):

    modules_per_string = input[0]
    strings = input[1]

    pvmodel = pv.default("PVBatteryResidential")

    pvmodel.SolarResource.solar_resource_file = script_path(
        "data/tmy_5.579_-0.233_2005_2014.epw"
    )

    pvmodel.Load.load = tuple(our_load_profile)

    pvmodel.Module.module_model = 1  # set it to CEC model

    pvmodel.Inverter.inverter_model = 0.0  # set it to CEC
    pvmodel.Inverter.inv_num_mppt = 1  # use single mmpts

    ## Max number of modules in a string
    max_modules_in_string = (
        pvmodel.Inverter.mppt_hi_inverter
        / pvmodel.CECPerformanceModelWithModuleDatabase.cec_v_oc_ref
    )

    ## Min number of modules in a string
    min_modules_in_string = (
        pvmodel.Inverter.mppt_low_inverter
        / pvmodel.CECPerformanceModelWithModuleDatabase.cec_v_oc_ref
    )

    assert modules_per_string > min_modules_in_string
    assert modules_per_string < max_modules_in_string

    # System Design
    pvmodel.SystemDesign.inverter_count = inverters

    pvmodel.SystemDesign.subarray1_modules_per_string = modules_per_string
    pvmodel.SystemDesign.subarray1_nstrings = strings
    pvmodel.SystemDesign.subarray1_mppt_input = 1
    pvmodel.SystemDesign.subarray1_track_mode = 0  # fixed tracking

    pvmodel.SystemDesign.subarray2_enable = 1
    pvmodel.SystemDesign.subarray2_modules_per_string = modules_per_string
    pvmodel.SystemDesign.subarray2_nstrings = strings
    pvmodel.SystemDesign.subarray2_mppt_input = 1
    pvmodel.SystemDesign.subarray2_track_mode = 0  # fixed tracking

    pvmodel.SystemDesign.subarray3_enable = 1
    pvmodel.SystemDesign.subarray3_modules_per_string = modules_per_string
    pvmodel.SystemDesign.subarray3_nstrings = strings
    pvmodel.SystemDesign.subarray3_mppt_input = 1
    pvmodel.SystemDesign.subarray3_track_mode = 0  # fixed tracking

    pvmodel.SystemDesign.subarray4_enable = 1
    pvmodel.SystemDesign.subarray4_modules_per_string = modules_per_string
    pvmodel.SystemDesign.subarray4_nstrings = strings
    pvmodel.SystemDesign.subarray4_mppt_input = 1
    pvmodel.SystemDesign.subarray4_track_mode = 0  # fixed tracking

    mod_power_rating = (
        pvmodel.CECPerformanceModelWithModuleDatabase.cec_v_mp_ref
        * pvmodel.CECPerformanceModelWithModuleDatabase.cec_i_mp_ref
    )
    pvmodel.SystemDesign.system_capacity = (
        mod_power_rating * 4 * modules_per_string * strings
    )

    pvmodel.BatterySystem.batt_current_charge_max = 24
    pvmodel.BatterySystem.batt_current_discharge_max = 24

    pvmodel.BatterySystem.batt_power_charge_max_kwac = 12
    pvmodel.BatterySystem.batt_power_discharge_max_kwac = 11

    pvmodel.BatterySystem.batt_power_charge_max_kwdc = 12
    pvmodel.BatterySystem.batt_power_discharge_max_kwdc = 12

    pvmodel.BatterySystem.en_batt = 1

    #     pvmodel.BatterySystem.batt_computed_bank_capacity = batt_bank_capacity # kWh
    #     pvmodel.BatterySystem.batt_computed_series = 139
    #     pvmodel.BatterySystem.batt_computed_strings = 48
    #     pvmodel.BatterySystem.batt_power_charge_max_kwac = 10.417
    #     pvmodel.BatterySystem.batt_power_discharge_max_kwac = 9.6
    #     pvmodel.BatterySystem.batt_power_charge_max_kwdc = 9.982
    #     pvmodel.BatterySystem.batt_power_discharge_max_kwdc = 9.982

    pvmodel.BatteryDispatch.batt_dispatch_choice = 4.0  # manual discharge
    pvmodel.BatteryDispatch.dispatch_manual_charge = (1, 1, 1, 1, 0, 0)
    pvmodel.BatteryDispatch.dispatch_manual_discharge = (1, 1, 1, 1, 0, 0)
    pvmodel.BatteryDispatch.dispatch_manual_percent_discharge = (25, 25, 25, 75)

    pvmodel.execute()

    uptime_hours = np.count_nonzero(
        (
            np.array(pvmodel.Outputs.system_to_load)
            + np.array(pvmodel.Outputs.batt_to_load)
            - np.tile(our_load_profile, 25)  # repeat load profile for 25 years
        )
        == 0
    )

    uptime_percent = uptime_hours / (365 * 24 * 25)  # percent uptime for 25 years

    return (uptime_percent, uptime_hours, modules_per_string, strings, inverters)


@task
def create_output_dict(
    uptime_percent, uptime_hours, modules_per_string, strings, inverters
):
    details = [
        {
            "uptime_percent": uptime_percent,
            "uptime_hours": uptime_hours,
            "modules_per_string": modules_per_string,
            "strings": strings,
            "inverters": inverters,
        }
    ]
    return details


@task
def save_dict(details):
    with open("ghana_model.json", "w") as f:
        json.dump(details, f)


with Flow("Ghana-Model") as flow:
    our_load_profile = load_profile()
    inputs = generate_modules_X_strings()
    model_outputs = execute_pvmodel.map(inputs, unmapped(our_load_profile))
    details = create_output_dict(
        model_outputs[0],
        model_outputs[1],
        model_outputs[2],
        model_outputs[3],
        model_outputs[4],
    )
    save_dict(details)


if __name__ == "__main__":
    flow.run(executor=LocalDaskExecutor(scheduler="processes", num_workers=16))
