import tkinter as tki
import tkcalendar as cal

class AddPosition(object):

    root = None

    def __init__(self, dict_key=None):
        """
        dict_key = <sequence> (dictionary, key) to associate with position
        (providing a sequence for dict_key creates an entry for user input)
        """
        # tki = tkinter
        self.top = tki.Toplevel(AddPosition.root)
        self.top.grab_set()

        frm = tki.Frame(self.top, borderwidth=4, relief='ridge')
        frm.pack(fill='both', expand=True)
        msg = "Enter option information for {0} with expiration {1}".format(dict_key["symbol"], dict_key["expiration_str"])
        label = tki.Label(frm, text=msg)
        label.grid(row=0, column = 0, ipadx=10, padx=4, pady=4)

        caller_wants_an_entry = dict_key is not None

        if caller_wants_an_entry:
            label_strike = tki.Label(frm, text="Strike Price")
            label_strike.grid(row=1, column=0, padx=5, pady=5)
            self.strike_entry = tki.Entry(frm)
            self.strike_entry.grid(row=1, column= 1, padx=5, pady=5)

            label_price = tki.Label(frm, text="Option Price")
            label_price.grid(row=2, column=0, padx=5, pady=5)
            self.price_entry = tki.Entry(frm)
            self.price_entry.grid(row=2, column= 1, padx=5, pady=5)

            label_date = tki.Label(frm, text="Open date")
            label_date.grid(row=3, column=0, padx=5, pady=5)
            self.open_date = cal.DateEntry(frm, width=12, background='darkblue',
                                           foreground='white', borderwidth=2, year=2020)
            self.open_date.grid(row=3, column=1, padx=5, pady=5)

            self.buy_sell_value = tki.IntVar(frm)
            self.buy_sell_value.set(2)

            self.buy_radio = tki.Radiobutton(frm,
                                             text="Buy",
                                             padx=5,
                                             variable=self.buy_sell_value,
                                             value=1)
            self.buy_radio.grid(row=4, column=0, padx=5, pady=5)

            self.sell_radio = tki.Radiobutton(frm,
                                             text="Sell",
                                             padx=5,
                                             variable=self.buy_sell_value,
                                             value=2)
            self.sell_radio.grid(row=4, column=1, padx=5, pady=5)

            self.put_call_value = tki.IntVar(frm)
            self.put_call_value.set(1)

            self.call_radio = tki.Radiobutton(frm,
                                             text="Call",
                                             padx=5,
                                             variable=self.put_call_value,
                                             value=1)
            self.call_radio.grid(row=5, column=0, padx=5, pady=5)

            self.put_radio = tki.Radiobutton(frm,
                                             text="Put",
                                             padx=5,
                                             variable=self.put_call_value,
                                             value=2)
            self.put_radio.grid(row=5, column=1, padx=5, pady=5)


            b_ok = tki.Button(frm, text='Ok')
            b_ok['command'] = lambda: self.entry_to_dict(dict_key)
            b_ok.grid(row=6, column= 0)

            b_cancel = tki.Button(frm, text='Cancel')
            b_cancel['command'] = self.top.destroy
            b_cancel.grid(row=6, column= 1)

    def entry_to_dict(self, dict_key):
        try:
            strike = float(self.strike_entry.get())
            price = float(self.price_entry.get())
            dict_key["option_price"] = price
            dict_key["strike_price"] = strike
            dict_key["open_date"] = self.open_date.get()
            dict_key["put_call"] = "put" if self.put_call_value.get() == 2 else "call"
            dict_key["buy_sell"] = "sell" if self.buy_sell_value.get() == 2 else "buy"
            dict_key["added"] = True
            self.top.destroy()
        except ValueError:
            self.strike_entry.focus_set()
