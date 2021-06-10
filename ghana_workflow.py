from metaflow import FlowSpec, step, IncludeFile, Parameter


def script_path(filename):
    """
    A convenience function to get the absolute path to a file in this
    tutorial's directory. This allows the tutorial to be launched from any
    directory.
    """
    import os

    filepath = os.path.join(os.path.dirname(__file__))
    return os.path.join(filepath, filename)


class GhanaModelFlow(FlowSpec):

    # solar_resource_file = IncludeFile(
    #     "solar_resource_data",
    #     help="Path to solar resource data",
    #     default=script_path("data/tmy_5.579_-0.233_2005_2014.epw")
    # )

    load_profile = IncludeFile(
        "load_profile",
        help="Path to load profile",
        default=script_path("data/Max_load_profile_for_year.txt")
    )

    # modules_per_string = Parameter(
    #     "modules_per_string",
    #     help="Modules connected in series",
    #     default=5
    # )

    # strings = Parameter(
    #     "strings",
    #     help="Number of strings (in parallel)",
    #     default=6
    # )

    inverters = Parameter(
        "inverters",
        help="Number of inverters",
        default=4
    )


    @step
    def start(self):
        
        import numpy as np
        from io import StringIO
        import itertools

        self.our_load_profile = np.loadtxt(
            StringIO(self.load_profile), 
            skiprows=1
        )

        modules = range(2,8)
        strings = range(4,15)

        self.modules_X_strings = list(itertools.product(modules, strings))
        
        self.next(self.execute_pvmodel, foreach="modules_X_strings")


    @step
    def execute_pvmodel(self):
        
        import PySAM.Pvsamv1 as pv
        import numpy as np
        from io import StringIO


        self.modules_per_string = self.input[0]
        self.strings = self.input[1]

        pvmodel = pv.default('PVBatteryResidential')
        
        pvmodel.SolarResource.solar_resource_file = script_path("data/tmy_5.579_-0.233_2005_2014.epw")

        pvmodel.Load.load = tuple(self.our_load_profile)
        
        pvmodel.Module.module_model = 1 # set it to CEC model
        
        pvmodel.Inverter.inverter_model = 0. # set it to CEC
        pvmodel.Inverter.inv_num_mppt = 1 # use single mmpts
        
        
        ## Max number of modules in a string
        max_modules_in_string = pvmodel.Inverter.mppt_hi_inverter/pvmodel.CECPerformanceModelWithModuleDatabase.cec_v_oc_ref
        
        ## Min number of modules in a string
        min_modules_in_string = pvmodel.Inverter.mppt_low_inverter/pvmodel.CECPerformanceModelWithModuleDatabase.cec_v_oc_ref
        
        assert self.modules_per_string > min_modules_in_string
        assert self.modules_per_string < max_modules_in_string
        
        # System Design
        pvmodel.SystemDesign.inverter_count = self.inverters

        pvmodel.SystemDesign.subarray1_modules_per_string = self.modules_per_string
        pvmodel.SystemDesign.subarray1_nstrings = self.strings
        pvmodel.SystemDesign.subarray1_mppt_input = 1
        pvmodel.SystemDesign.subarray1_track_mode = 0 # fixed tracking

        pvmodel.SystemDesign.subarray2_enable = 1
        pvmodel.SystemDesign.subarray2_modules_per_string = self.modules_per_string
        pvmodel.SystemDesign.subarray2_nstrings = self.strings
        pvmodel.SystemDesign.subarray2_mppt_input = 1
        pvmodel.SystemDesign.subarray2_track_mode = 0 # fixed tracking

        pvmodel.SystemDesign.subarray3_enable = 1
        pvmodel.SystemDesign.subarray3_modules_per_string = self.modules_per_string
        pvmodel.SystemDesign.subarray3_nstrings = self.strings
        pvmodel.SystemDesign.subarray3_mppt_input = 1
        pvmodel.SystemDesign.subarray3_track_mode = 0 # fixed tracking

        pvmodel.SystemDesign.subarray4_enable = 1
        pvmodel.SystemDesign.subarray4_modules_per_string = self.modules_per_string
        pvmodel.SystemDesign.subarray4_nstrings = self.strings
        pvmodel.SystemDesign.subarray4_mppt_input = 1
        pvmodel.SystemDesign.subarray4_track_mode = 0 # fixed tracking
        
        mod_power_rating = pvmodel.CECPerformanceModelWithModuleDatabase.cec_v_mp_ref * pvmodel.CECPerformanceModelWithModuleDatabase.cec_i_mp_ref
        pvmodel.SystemDesign.system_capacity = mod_power_rating * 4 * self.modules_per_string * self.strings
        
        pvmodel.BatterySystem.batt_current_charge_max = 24
        pvmodel.BatterySystem.batt_current_discharge_max = 24

        pvmodel.BatterySystem.batt_power_charge_max_kwac = 12
        pvmodel.BatterySystem.batt_power_discharge_max_kwac= 11

        pvmodel.BatterySystem.batt_power_charge_max_kwdc = 12
        pvmodel.BatterySystem.batt_power_discharge_max_kwdc= 12

        pvmodel.BatterySystem.en_batt = 1
        
    #     pvmodel.BatterySystem.batt_computed_bank_capacity = batt_bank_capacity # kWh
    #     pvmodel.BatterySystem.batt_computed_series = 139
    #     pvmodel.BatterySystem.batt_computed_strings = 48
    #     pvmodel.BatterySystem.batt_power_charge_max_kwac = 10.417
    #     pvmodel.BatterySystem.batt_power_discharge_max_kwac = 9.6
    #     pvmodel.BatterySystem.batt_power_charge_max_kwdc = 9.982
    #     pvmodel.BatterySystem.batt_power_discharge_max_kwdc = 9.982
        
        pvmodel.BatteryDispatch.batt_dispatch_choice = 4.0 # manual discharge
        pvmodel.BatteryDispatch.dispatch_manual_charge = (1, 1, 1, 1, 0, 0)
        pvmodel.BatteryDispatch.dispatch_manual_discharge = (1, 1, 1, 1, 0, 0)
        pvmodel.BatteryDispatch.dispatch_manual_percent_discharge = (25, 25, 25, 75)
        
        pvmodel.execute()

        # Why can't I pickle pysam objects!!!!!!!
        # self.pvmodel = pvmodel

        self.uptime_hours = np.count_nonzero(
            (np.array(pvmodel.Outputs.system_to_load) + 
            np.array(pvmodel.Outputs.batt_to_load) - 
            np.tile(self.our_load_profile, 25)  # repeat load profile for 25 years
            ) == 0
            )
        
        self.uptime_percent = self.uptime_hours/(365 * 24 * 25)  # percent uptime for 25 years

        self.next(self.join)
    
    @step
    def join(self, inputs):
        "Join parallel branches"

        # self.uptime_stats = [inp.uptime_percent for inp in inputs]
        self.details = [{
            "uptime_percent" : inp.uptime_percent,
            "modules_per_string" : inp.modules_per_string,
            "strings" : inp.strings,
            "inverters" : inp.inverters
            } for inp in inputs
        ]

        self.next(self.end)

    @step
    def end(self):
        pass


if __name__ == "__main__":
    GhanaModelFlow()
