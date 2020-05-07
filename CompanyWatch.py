class CompanyWatch():
    """ Declares the companies to be watched """
    def __init__(self):
        self.company_list = [{"symbol": "INTC", "name": "Intel"},
                             {"symbol": "LITE", "name": "Lumentum"},
                             {"symbol": "AAPL", "name": "Apple"},
                             {"symbol": "MSFT", "name": "Microsoft"},
                             {"symbol": "MAR", "name": "Marriot"}]

    def get_companies(self):
        """ Returns the companies """
        return self.company_list

