class OptionsScreenerWatch:
    """ Declares the companies to be watched """
    def __init__(self):
        self.options_list = [
            {"symbol": "QQQ", "name": "Invesco QQQ"},
            {"symbol": "MAR", "name": "Marriot"},
            {"symbol": "TSLA", "name": "Tesla Motor"},
            {"symbol": "SNAP", "name": "Snap Corp"},
            {"symbol": "WORK", "name": "Slack Technologies"},
            {"symbol": "AMD", "name": "Advanced Micro Devices"},
            {"symbol": "LITE", "name": "Lumentum technologies"},
            {"symbol": "INTC", "name": "Intel Corporation"},
            {"symbol": "TSM", "name": "Taiwan semiconductor"},
            {"symbol": "BLNK", "name": "Blink Charging Co"},
            {"symbol": "PCG", "name": "PG&E Co"},
            {"symbol": "CSCO", "name": "Cisco Systems"},
            {"symbol": "SPWR", "name": "SunPower"},
            {"symbol": "NVDA", "name": "NVidia"},
            {"symbol": "SNAP", "name": "Snap Corp"}
        ]

    def get_companies(self):
        """ Returns the companies """
        return self.options_list

