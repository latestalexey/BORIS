'''

https://stackoverflow.com/questions/41156260/how-to-use-a-qthread-to-update-a-matplotlib-figure-with-pyqt

'''


from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import sys
import numpy as np
import time

from utilities import check_txt_file


class MyMplCanvas(FigureCanvas):

    def __init__(self, parent=None):
        self.fig = Figure()
        self.axes = self.fig.add_subplot(1,1,1)
        
        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)


class Plot_data(QWidget):
    send_fig = pyqtSignal(float)

    def __init__(self, file_name, interval, color, plot_title, y_label, columns_to_plot):
        super(Plot_data, self).__init__()

        self.myplot = MyMplCanvas(self)

        self.layout = QGridLayout()
        self.layout.addWidget(self.myplot)
        
        self.color = color
        self.plot_title = plot_title
        self.y_label = y_label
        
        r = check_txt_file(file_name)

        all_data = np.loadtxt(file_name, delimiter=r["separator"])
        
        time_column_idx = int(columns_to_plot.split(",")[0]) - 1
        value_column_idx = int(columns_to_plot.split(",")[-1]) - 1
        
        print("time_column_idx,value_column_idx", time_column_idx,value_column_idx)

        data = all_data[:, [time_column_idx, value_column_idx]] # time in 1st column, value in 2nd
        
        del all_data

        min_value, max_value = min(data[:,1]), max(data[:,1])

        period = round((data[-1, 0] - data[0, 0]) / len(data),4)

        max_frequency = 1 / period

        time_interval = interval * max_frequency

        # plotter and thread are none at the beginning
        self.plotter = Plotter()
        self.plotter.data = data
        self.plotter.max_frequency = max_frequency
        self.plotter.time_interval = time_interval
        self.plotter.min_value = min_value
        self.plotter.max_value = max_value
        self.timer_started_at = time.time()

        self.thread = QThread()

        # connect signals
        self.send_fig.connect(self.plotter.replot)
        self.plotter.return_fig.connect(self.plot)
        #move to thread and start
        self.plotter.moveToThread(self.thread)
        self.thread.start()

    def update_plot(self, time_):
        """
        update plot by emeting a signal
        """
        self.send_fig.emit(time_)
        
    def close_plot(self):
        self.thread.quit()
        self.thread.wait()
        self.close()


    # Slot receives data and plots it
    def plot(self, x, y, position_data, position_start, min_value, max_value, position_end, max_frequency):
        self.myplot.axes.clear()
        
        self.myplot.axes.set_title(self.plot_title)
        
        self.myplot.axes.set_xlim(position_start , position_end)

        self.myplot.axes.set_xticklabels([str(int(w / max_frequency)) for w in self.myplot.axes.get_xticks()])

        self.myplot.axes.set_ylim((min_value, max_value))
        
        self.myplot.axes.set_ylabel(self.y_label)
        
        self.myplot.axes.axvline(x=position_data, color="red", linestyle='-')

        self.myplot.axes.plot(x, y, self.color)

        self.myplot.draw()


class Plotter(QObject):
    return_fig = pyqtSignal(object, object, int, float, float, float, float, float)

    @pyqtSlot(float)
    def replot(self, time_): # time_ in s

        current_time = time_
               
        position_data = int(current_time * self.max_frequency)

        position_start = position_data - self.time_interval // 2
        position_end = position_data + self.time_interval // 2
        
        if position_start < 0:
            data1 = 0
            data2 = int(position_start + self.time_interval)
        else:
            data1 = int(position_start)
            data2 = int(position_end)

        self.return_fig.emit(np.arange(data1, data2, 1), self.data[ data1:data2][:,1],
                             position_data,
                             position_start,
                             self.min_value, self.max_value,
                             position_end, self.max_frequency)

        

if __name__ == '__main__':
    app = QApplication(sys.argv)
    plot_data = Plot_data("ecg_converted.tsv", 60, "b-", "aa", "y lab")
    
    plot_data.show()

    plot_data2 = Plot_data("ecg_converted2.tsv", 120, "r-", "bb", "y lab")
    
    plot_data2.show()

    plot_data.start_update()
    plot_data2.start_update()


    sys.exit(app.exec_())
