class OptionsScreenerWatch:
    """ Declares the companies to be watched """
    def __init__(self):
        self.options_list = [
            {"symbol": "QQQ", "name": "Invesco QQQ"},
            {"symbol": "MAR", "name": "Marriot"},
            {"symbol": "TSLA", "name": "Tesla Motor"},
            {"symbol": "T", "name": "AT&T"},
            {"symbol": "VZ", "name": "Verizon"},
            {"symbol": "AMD", "name": "Advanced Micro Devices"},
            {"symbol": "LITE", "name": "Lumentum technologies"}
        ]

    def get_companies(self):
        """ Returns the companies """
        return self.options_list
