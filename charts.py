
import matplotlib.pyplot as plt


class Charts():
    def __init__(self):
        self.axes = None
        self.fig = None

    def create_chart(self, rows: int, columns: int, title: str) -> object:
        fig, axes = plt.subplots(rows, columns)
        self.axes = axes
        self.fig = fig
        fig.suptitle(title, fontsize=14)

    def plot_data_time_series(self, row: int, column: int, time_series: [], data: [], color: object, label: str) -> object:
        self.axes[row][column].plot(time_series, data, label=label, color=color)
        self.axes[row][column].legend(loc='best')
        plt.ion()
        plt.pause(0.00001)
        plt.show()

    def plot_min_max(self, row: int, column: int, time_series: [], data: [], color: str, label: str) -> object:
        self.axes[row][column].plot(time_series, data, color, label=label)
        self.axes[row][column].legend(loc='best')
        plt.ion()
        plt.pause(0.00001)
        plt.show()

# def show_ica_charts():
#     (red_input, green_input) = read_input("icainput.txt")
#     (red_output, green_output) = read_output("icaoutput.txt")
#     print("foo")
#
#     #
#     fig, ax = plt.subplots(2, 1)
#     fig.suptitle("ICA Input", fontsize=14)
#     #
#     #
#     # ax[0].plot( blue_series, label='Normalized Raw Blue data', color=(0,0,1))
#     ax[0].plot( red_input, label='Red data', color=(1,0,0))
#     ax[0].plot( green_input, label='Green data', color=(0,1,0))
#     #    #
#     #
#     ax[1].plot( red_output, label='ICA Red data', color=(1,0,0))
#     ax[1].plot( green_output, label='ICAGreen data', color=(0,1,0))
#     #
#     ax[0].legend(loc = 'best')
#     ax[1].legend(loc = 'best')
#     #
#     plt.ion()
#     plt.pause(0.00001)
#     plt.show()
