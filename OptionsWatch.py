class OptionsWatch:
    """ Declares the companies to be watched """
    def __init__(self):
        self.options_list = [
            {"symbol": "QQQ", "name": "Invesco QQQ"},
            {"symbol": "MAR", "name": "Marriot"},
            {"symbol": "TSLA", "name": "Tesla Motor"},
            {"symbol": "NVDA", "name": "NVida Corporation"},
            {"symbol": "LITE", "name": "Lumentum Corp"},
            {"symbol": "AMD", "name": "Advanced Micro Devices"},
            {"symbol": "BLNK", "name": "Blink charging"},
            {"symbol": "PCG", "name": "PG&E corporation"},
            {"symbol": "SPWR", "name": "SunPower"}

        ]

    def get_companies(self):
        """ Returns the companies """
        return self.options_list

