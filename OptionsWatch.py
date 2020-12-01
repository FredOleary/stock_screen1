class OptionsWatch:
    """ Declares the companies to be watched """
    def __init__(self):
        self.options_list = [
            {"symbol": "QQQ", "name": "Invesco QQQ"},
            {"symbol": "MAR", "name": "Marriot"},
            {"symbol": "TSLA", "name": "Tesla Motor"},
            {"symbol": "T", "name": "AT&T"}
        ]

    def get_companies(self):
        """ Returns the companies """
        return self.options_list

