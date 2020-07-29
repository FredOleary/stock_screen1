class CompanyWatch:
    """ Declares the companies to be watched """
    def __init__(self):
        self.company_list = [
            # {"symbol": "INTC", "name": "Intel"},
            # {"symbol": "LITE", "name": "Lumentum"},
            # {"symbol": "VOO", "name": "Vanguard S&P 500 ETF"},
            {"symbol": "AMD", "name": "Advanced Micro Devices"},
            {"symbol": "GE", "name": "General Electric Corp"},
            {"symbol": "QQQ", "name": "Invesco QQQ"},
            {"symbol": "IWM", "name": "iShares Russell 2000 ETF"},
            {"symbol": "VIG", "name": "Vanguard dividend appreciation"},
            {"symbol": "MAR", "name": "Marriot"}
        ]

    def get_companies(self):
        """ Returns the companies """
        return self.company_list

