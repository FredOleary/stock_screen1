class OptionsConfiguration:
    """ Tuning paramters for the various utilities """
    def __init__(self):
        self.options_config = {"collector_update_rate_in_seconds": 900,
                               "collector_look_ahead_expirations": 3,
                               "screener_look_ahead_expirations": 5,
                               "api_options": "APITradier",
                               "collector_start_time_pst": "06:15",
                               "collector_end_time_pst": "13:15",
                               "collector_exclude_days":[ "saturday", "sunday"] }




    def get_configuration(self):
        """ Returns the companies """
        return self.options_config

