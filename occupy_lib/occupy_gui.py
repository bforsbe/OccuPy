import mrcfile as mf
import numpy as np

from io import StringIO

from matplotlib.backends.qt_compat import QtWidgets
from matplotlib.figure import Figure

# Ensure using PyQt5 backend
import matplotlib
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as Canvas
matplotlib.use('QT5Agg')

from PyQt5 import QtCore, QtGui, QtWidgets
QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True) #enable highdpi scaling
QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True) #use highdpi icons

import os,sys
os.environ["QT_DEVICE_PIXEL_RATIO"] = "1"
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
os.environ["QT_SCREEN_SCALE_FACTORS"] = "1"
os.environ["QT_SCALE_FACTOR"] = "1" # larger than 1 makes it bigger

from occupy_lib import estimate, map_tools, occupancy, vis, solvent, extras, args   # for terminal use
from scipy import ndimage as ndi

class EMDB_dialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(EMDB_dialog, self).__init__(parent)
        self.id = None

    def make_dialog(self):
        self.setObjectName("Fetch EMDB")

        self.setWindowTitle("Fetch EMDB")
        self.setEnabled(True)
        self.resize(140,90)

        self.textEdit = QtWidgets.QLineEdit(self)
        self.textEdit.setGeometry(10,10,120,30)
        self.textEdit.setPlaceholderText("-")

        self.button = QtWidgets.QToolButton(self)
        self.button.setGeometry(10,50,120,30)
        self.button.setText("Fetch")
        self.button.clicked.connect(self.update_id)
        self.textEdit.returnPressed.connect(self.update_id)

    def update_id(self):
        self.id = self.textEdit.text()
        self.close()


class fullLog_dialog(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(fullLog_dialog, self).__init__(parent)
        self.id = None

    def make_dialog(self,file_name):
        import os
        self.setObjectName("Full Log")
        self.setWindowTitle(f'{os.getcwd()}/{file_name}')
        self.setEnabled(True)
        self.resize(600,1000)

        self.logText = QtWidgets.QTextEdit(self)
        self.logText.setGeometry(0,0,600,1000)

class Capturing(list):
    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = StringIO()
        return self

    def __exit__(self, *args):

        self.extend(self._stringio.getvalue().splitlines())
        del self._stringio  # free up some memory
        sys.stdout = self._stdout

# Matplotlib canvas class to create figure
class InputMapProperties():
    def __init__(self):
        self.voxel_size_ori = -1
        self.voxel_size_proc = -1
        self.lowpass = -1
        self.kernel_size = -1
        self.kernel_radius = -1
        self.kernel_nv = -1
        self.kernel_tau = -1

# Matplotlib canvas class to create figure
class MplCanvas(Canvas):
    def __init__(self):
        self.fig = Figure()
        self.ax = self.fig.add_axes([0.15, 0.13, 0.8, 0.85])
        #self.fig.tight_layout()

        Canvas.__init__(self, self.fig)
        Canvas.setSizePolicy(self, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        Canvas.updateGeometry(self)

# Matplotlib widget
class MplWidget(QtWidgets.QWidget):
    def __init__(self,parent=None):
        QtWidgets.QWidget.__init__(self, parent)   # Inherit from QWidget
        self.canvas = MplCanvas()                  # Create canvas object
        self.vbl = QtWidgets.QVBoxLayout()         # Set box for plotting
        self.vbl.addWidget(self.canvas)
        self.setLayout(self.vbl)

        self.amplify = False
        self.amplification_power=2.0

        self.attenuate = False
        self.attenuation_power=2.0

        self.sigmoid = False
        self.sigmoid_power=3.0
        self.sigmoid_pivot=0.2

    def update_sigmoid_power(self, power):
        self.sigmoid = True
        self.sigmoid_power = power # self.parent.horizontalSlider_3.value()
        self.plot_modification()
        #self.sigmoid_power = self.parent().horizontalSlider_5.value()

    def update_sigmoid_pivot(self, pivot):
        self.sigmoid = True
        self.sigmoid_pivot = pivot / 100.0 # self.parent.horizontalSlider_3.value()
        self.plot_modification()


    def update_amplification_power(self, power):
        self.amplify = True
        self.amplification_power = power
        self.plot_modification()

    def update_attenuation_power(self, power):
        self.attenuate = True
        self.attenuation_power = power
        self.plot_modification()



    def plot_modification(self):

        self.canvas.ax.clear()
        x = np.linspace(0, 1, 100)
        if self.amplify:
            self.canvas.ax.plot(x, x ** (1 / self.amplification_power), 'C0')

        if self.attenuate:
            self.canvas.ax.plot(x, x ** (self.attenuation_power), 'C1')

        if self.sigmoid:
            x, y = occupancy.scale_mapping_sigmoid(self.sigmoid_pivot,self.sigmoid_power)
            self.canvas.ax.plot(x, y, 'C2')
            self.canvas.ax.plot(self.sigmoid_pivot, self.sigmoid_pivot, 'ko')

        self.canvas.ax.plot([0, 1], [0, 1], 'k--')
        self.canvas.ax.set_xlabel('estimated input scale')
        self.canvas.ax.set_ylabel('modified output scale')

        self.canvas.draw()





class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        from pathlib import Path
        MainWindow.setObjectName("MainWindow")
        MainWindow.setEnabled(True)
        MainWindow.resize(684, 821)
        MainWindow.setAcceptDrops(True)
        MainWindow.setFixedSize(684, 821)
        self.icon_small = QtGui.QIcon()
        icon_image_small = f'{Path(__file__).parent.parent}/resources/occupy_icon_small.png'
        self.icon_small.addPixmap(QtGui.QPixmap(icon_image_small), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.icon_chimX = QtGui.QIcon()
        chimX_image = f'{Path(__file__).parent.parent}/resources/chimX.png'
        self.icon_chimX.addPixmap(QtGui.QPixmap(chimX_image), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        MainWindow.setWindowIcon(self.icon_small)

        self.icon_large = f'{Path(__file__).parent.parent}/resources/occupy_icon.png'
        self.new_session = True

        self.os = None

        self.inputMap = InputMapProperties()
        self.infile_size = None
        self.infile_minval = None
        self.infile_maxval = None
        self.log_file_name = 'occupy_gui_log.txt'
        self.confidence_file_name = None
        self.chimerax_file_name = None
        self.solModel_file_name = None
        self.scale_file_name = None
        self.occ_scale = None
        self.res_scale = None
        self.chimerax_name = None

        self.cmd = []
        self.run_no = 0

        # Input map
        self.horizontalLayoutWidget = QtWidgets.QWidget(MainWindow)
        self.horizontalLayoutWidget.setGeometry(QtCore.QRect(90, 30, 581, 31))
        self.horizontalLayoutWidget.setObjectName("horizontalLayoutWidget")
        self.horizontalLayout_inputMap = QtWidgets.QHBoxLayout(self.horizontalLayoutWidget)
        self.horizontalLayout_inputMap.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_inputMap.setObjectName("horizontalLayout_inputMap")
        self.comboBox_inputMap = QtWidgets.QComboBox(self.horizontalLayoutWidget)
        self.comboBox_inputMap.setObjectName("comboBox_inputMap")
        self.horizontalLayout_inputMap.addWidget(self.comboBox_inputMap, 0, QtCore.Qt.AlignVCenter)
        self.toolButton_inputMap_browse = QtWidgets.QToolButton(self.horizontalLayoutWidget)
        self.toolButton_inputMap_browse.setObjectName("toolButton_inputMap_browse")
        self.horizontalLayout_inputMap.addWidget(self.toolButton_inputMap_browse)
        self.toolButton_inputMap_emdb = QtWidgets.QToolButton(self.horizontalLayoutWidget)
        self.toolButton_inputMap_emdb.setObjectName("toolButton_inputMap_emdb")
        self.horizontalLayout_inputMap.addWidget(self.toolButton_inputMap_emdb)

        bold = QtGui.QFont()
        bold.setBold(True)
        self.label_modTitle = QtWidgets.QLabel(MainWindow)
        self.label_modTitle.setGeometry(QtCore.QRect(10, 270, 261, 30))
        self.label_modTitle.setText("Modification options")
        self.label_modTitle.setFont(bold)

        self.label_kernelTitle = QtWidgets.QLabel(MainWindow)
        self.label_kernelTitle.setGeometry(QtCore.QRect(10, 70, 261, 30))
        self.label_kernelTitle.setText("Scale kernel settings")
        self.label_kernelTitle.setFont(bold)

        self.label_kernelTitle = QtWidgets.QLabel(MainWindow)
        self.label_kernelTitle.setGeometry(QtCore.QRect(10, 466, 261, 30))
        self.label_kernelTitle.setText("Optional/extra options")
        self.label_kernelTitle.setFont(bold)


        self.tabWidget_modification = QtWidgets.QTabWidget(MainWindow)
        self.tabWidget_modification.setGeometry(QtCore.QRect(10, 300, 261, 131))
        self.tabWidget_modification.setObjectName("tabWidget_modification")
        self.tab_amplification = QtWidgets.QWidget()
        self.tab_amplification.setObjectName("tab_amplification")
        self.groupBox_amplification = QtWidgets.QGroupBox(self.tab_amplification)
        self.groupBox_amplification.setGeometry(QtCore.QRect(0, 10, 241, 81))
        self.groupBox_amplification.setTitle("")
        self.groupBox_amplification.setCheckable(True)
        self.groupBox_amplification.setChecked(False)
        self.groupBox_amplification.setObjectName("groupBox_amplification")
        self.gridLayoutWidget_3 = QtWidgets.QWidget(self.groupBox_amplification)
        self.gridLayoutWidget_3.setGeometry(QtCore.QRect(0, 20, 241, 61))
        self.gridLayoutWidget_3.setObjectName("gridLayoutWidget_3")
        self.gridLayout_amplification = QtWidgets.QGridLayout(self.gridLayoutWidget_3)
        self.gridLayout_amplification.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_amplification.setObjectName("gridLayout_amplification")
        self.doubleSpinBox_amplPower = QtWidgets.QDoubleSpinBox(self.gridLayoutWidget_3)
        self.doubleSpinBox_amplPower.setDecimals(1)
        self.doubleSpinBox_amplPower.setMinimum(1.0)
        self.doubleSpinBox_amplPower.setSingleStep(0.1)
        self.doubleSpinBox_amplPower.setMaximum(30.0)
        self.doubleSpinBox_amplPower.setProperty("value", 1.0)
        self.doubleSpinBox_amplPower.setObjectName("doubleSpinBox_amplPower")
        self.gridLayout_amplification.addWidget(self.doubleSpinBox_amplPower, 0, 2, 1, 1)
        self.label_amplPower = QtWidgets.QLabel(self.gridLayoutWidget_3)
        self.label_amplPower.setEnabled(True)
        self.label_amplPower.setObjectName("label_amplPower")
        self.gridLayout_amplification.addWidget(self.label_amplPower, 0, 0, 1, 1)
        self.horizontalSlider_amplPower = QtWidgets.QSlider(self.gridLayoutWidget_3)
        self.horizontalSlider_amplPower.setMinimum(10)
        self.horizontalSlider_amplPower.setMaximum(300)
        self.horizontalSlider_amplPower.setSingleStep(1)
        self.horizontalSlider_amplPower.setPageStep(10)
        self.horizontalSlider_amplPower.setProperty("value", 10)
        self.horizontalSlider_amplPower.setOrientation(QtCore.Qt.Horizontal)
        self.horizontalSlider_amplPower.setObjectName("horizontalSlider_amplPower")
        self.gridLayout_amplification.addWidget(self.horizontalSlider_amplPower, 0, 1, 1, 1)
        self.tabWidget_modification.addTab(self.tab_amplification, "")
        self.tab_attenuation = QtWidgets.QWidget()
        self.tab_attenuation.setObjectName("tab_attenuation")
        self.groupBox_attenuation = QtWidgets.QGroupBox(self.tab_attenuation)
        self.groupBox_attenuation.setGeometry(QtCore.QRect(0, 10, 241, 81))
        self.groupBox_attenuation.setTitle("")
        self.groupBox_attenuation.setCheckable(True)
        self.groupBox_attenuation.setChecked(False)
        self.groupBox_attenuation.setObjectName("groupBox_attenuation")
        self.gridLayoutWidget_4 = QtWidgets.QWidget(self.groupBox_attenuation)
        self.gridLayoutWidget_4.setGeometry(QtCore.QRect(0, 20, 241, 60))
        self.gridLayoutWidget_4.setObjectName("gridLayoutWidget_4")
        self.gridLayout_attenuation = QtWidgets.QGridLayout(self.gridLayoutWidget_4)
        self.gridLayout_attenuation.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_attenuation.setObjectName("gridLayout_attenuation")
        self.label_attnPower = QtWidgets.QLabel(self.gridLayoutWidget_4)
        self.label_attnPower.setEnabled(True)
        self.label_attnPower.setObjectName("label_attnPower")
        self.gridLayout_attenuation.addWidget(self.label_attnPower, 0, 0, 1, 1)
        self.doubleSpinBox_attnPower = QtWidgets.QDoubleSpinBox(self.gridLayoutWidget_4)
        self.doubleSpinBox_attnPower.setDecimals(1)
        self.doubleSpinBox_attnPower.setMinimum(1.0)
        self.doubleSpinBox_attnPower.setMaximum(30.0)
        self.doubleSpinBox_attnPower.setProperty("value", 1.0)
        self.doubleSpinBox_attnPower.setObjectName("doubleSpinBox_attnPower")
        self.gridLayout_attenuation.addWidget(self.doubleSpinBox_attnPower, 0, 2, 1, 1)
        self.horizontalSlider_attnPower = QtWidgets.QSlider(self.gridLayoutWidget_4)
        self.horizontalSlider_attnPower.setMinimum(10)
        self.horizontalSlider_attnPower.setMaximum(300)
        self.horizontalSlider_attnPower.setSingleStep(10)
        self.horizontalSlider_attnPower.setOrientation(QtCore.Qt.Horizontal)
        self.horizontalSlider_attnPower.setObjectName("horizontalSlider_attnPower")
        self.gridLayout_attenuation.addWidget(self.horizontalSlider_attnPower, 0, 1, 1, 1)
        self.tabWidget_modification.addTab(self.tab_attenuation, "")
        self.tab_sigmoid = QtWidgets.QWidget()
        self.tab_sigmoid.setObjectName("tab_sigmoid")
        self.groupBox_sigmoid = QtWidgets.QGroupBox(self.tab_sigmoid)
        self.groupBox_sigmoid.setGeometry(QtCore.QRect(0, 10, 241, 81))
        self.groupBox_sigmoid.setTitle("")
        self.groupBox_sigmoid.setCheckable(True)
        self.groupBox_sigmoid.setChecked(False)
        self.groupBox_sigmoid.setObjectName("groupBox_sigmoid")
        self.gridLayoutWidget_5 = QtWidgets.QWidget(self.groupBox_sigmoid)
        self.gridLayoutWidget_5.setGeometry(QtCore.QRect(0, 20, 241, 60))
        self.gridLayoutWidget_5.setObjectName("gridLayoutWidget_5")
        self.gridLayout_sigmoid = QtWidgets.QGridLayout(self.gridLayoutWidget_5)
        self.gridLayout_sigmoid.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_sigmoid.setObjectName("gridLayout_sigmoid")
        self.horizontalSlider_sigmoidPower = QtWidgets.QSlider(self.gridLayoutWidget_5)
        self.horizontalSlider_sigmoidPower.setMinimum(10)
        self.horizontalSlider_sigmoidPower.setMaximum(300)
        self.horizontalSlider_sigmoidPower.setSingleStep(10)
        self.horizontalSlider_sigmoidPower.setOrientation(QtCore.Qt.Horizontal)
        self.horizontalSlider_sigmoidPower.setObjectName("horizontalSlider_sigmoidPower")
        self.gridLayout_sigmoid.addWidget(self.horizontalSlider_sigmoidPower, 0, 1, 1, 1)
        self.doubleSpinBox_sigmoidPivot = QtWidgets.QDoubleSpinBox(self.gridLayoutWidget_5)
        self.doubleSpinBox_sigmoidPivot.setDecimals(2)
        self.doubleSpinBox_sigmoidPivot.setMinimum(0.01)
        self.doubleSpinBox_sigmoidPivot.setMaximum(0.99)
        self.doubleSpinBox_sigmoidPivot.setSingleStep(0.01)
        self.doubleSpinBox_sigmoidPivot.setProperty("value", 0.20)
        self.doubleSpinBox_sigmoidPivot.setObjectName("doubleSpinBox_sigmoidPivot")
        self.gridLayout_sigmoid.addWidget(self.doubleSpinBox_sigmoidPivot, 1, 2, 1, 1)
        self.horizontalSlider_sigmoidPivot = QtWidgets.QSlider(self.gridLayoutWidget_5)
        self.horizontalSlider_sigmoidPivot.setMinimum(1)
        self.horizontalSlider_sigmoidPivot.setMaximum(99)
        self.horizontalSlider_sigmoidPivot.setPageStep(1)
        self.horizontalSlider_sigmoidPivot.setProperty("value", 20)
        self.horizontalSlider_sigmoidPivot.setOrientation(QtCore.Qt.Horizontal)
        self.horizontalSlider_sigmoidPivot.setObjectName("horizontalSlider_sigmoidPivot")
        self.gridLayout_sigmoid.addWidget(self.horizontalSlider_sigmoidPivot, 1, 1, 1, 1)
        self.label_sigmoidPower = QtWidgets.QLabel(self.gridLayoutWidget_5)
        self.label_sigmoidPower.setEnabled(True)
        self.label_sigmoidPower.setObjectName("label_sigmoidPower")
        self.gridLayout_sigmoid.addWidget(self.label_sigmoidPower, 0, 0, 1, 1)
        self.label_sigmoidPivot = QtWidgets.QLabel(self.gridLayoutWidget_5)
        self.label_sigmoidPivot.setEnabled(True)
        self.label_sigmoidPivot.setObjectName("label_sigmoidPivot")
        self.gridLayout_sigmoid.addWidget(self.label_sigmoidPivot, 1, 0, 1, 1)
        self.doubleSpinBox_sigmoidPower = QtWidgets.QDoubleSpinBox(self.gridLayoutWidget_5)
        self.doubleSpinBox_sigmoidPower.setDecimals(1)
        self.doubleSpinBox_sigmoidPower.setMinimum(1.0)
        self.doubleSpinBox_sigmoidPower.setMaximum(30.0)
        self.doubleSpinBox_sigmoidPower.setProperty("value", 1.0)
        self.doubleSpinBox_sigmoidPower.setObjectName("doubleSpinBox_sigmoidPower")
        self.gridLayout_sigmoid.addWidget(self.doubleSpinBox_sigmoidPower, 0, 2, 1, 1)
        self.tabWidget_modification.addTab(self.tab_sigmoid, "")

        self.tabWidget_view = QtWidgets.QTabWidget(MainWindow)
        self.tabWidget_view.setEnabled(True)
        self.tabWidget_view.setGeometry(QtCore.QRect(280, 70, 391, 421))
        self.tabWidget_view.setMinimumSize(QtCore.QSize(319, 350))
        self.tabWidget_view.setMaximumSize(QtCore.QSize(10000, 10000))
        self.tabWidget_view.setObjectName("tabWidget_view")
        self.tab_viewInput = QtWidgets.QWidget()
        self.tab_viewInput.setEnabled(True)
        self.tab_viewInput.setObjectName("tab_viewInput")

        self.label_viewInput = QtWidgets.QLabel(self.tab_viewInput)
        self.label_viewInput.setGeometry(QtCore.QRect(0, 0, 391, 391))
        self.label_viewInput.setMinimumSize(QtCore.QSize(320, 320))
        self.label_viewInput.setMaximumSize(QtCore.QSize(1000, 1000))
        self.label_viewInput.setMouseTracking(False)
        self.label_viewInput.setFrameShape(QtWidgets.QFrame.Box)
        self.label_viewInput.setAlignment(QtCore.Qt.AlignCenter)
        self.label_viewInput.setEnabled(False)


        self.label_viewInput.setObjectName("label_viewInput")
        self.tabWidget_view.addTab(self.tab_viewInput, "")
        self.tab_viewScale = QtWidgets.QWidget()
        self.tab_viewScale.setEnabled(True)
        self.tab_viewScale.setObjectName("tab_viewScale")

        self.label_viewScale = QtWidgets.QLabel(self.tab_viewScale)
        self.label_viewScale.setGeometry(QtCore.QRect(0, 0, 391, 391))
        self.label_viewScale.setMinimumSize(QtCore.QSize(320, 320))
        self.label_viewScale.setMaximumSize(QtCore.QSize(1000, 1000))
        self.label_viewScale.setFrameShape(QtWidgets.QFrame.Box)
        self.label_viewScale.setAlignment(QtCore.Qt.AlignCenter)
        self.label_viewScale.setEnabled(False)

        self.label_viewScale.setObjectName("label_viewScale")
        self.tabWidget_view.addTab(self.tab_viewScale, "")
        self.tab_viewConfidence = QtWidgets.QWidget()
        self.tab_viewConfidence.setObjectName("tab_viewConfidence")

        self.label_viewConfidence = QtWidgets.QLabel(self.tab_viewConfidence)
        self.label_viewConfidence.setGeometry(QtCore.QRect(0, 0, 391, 391))
        self.label_viewConfidence.setMinimumSize(QtCore.QSize(320, 320))
        self.label_viewConfidence.setMaximumSize(QtCore.QSize(1000, 1000))
        self.label_viewConfidence.setFrameShape(QtWidgets.QFrame.Box)
        self.label_viewConfidence.setAlignment(QtCore.Qt.AlignCenter)
        self.label_viewConfidence.setEnabled(False)
        self.label_viewConfidence.setObjectName("label_viewConfidence")
        self.label_viewConfidence.raise_()

        self.tabWidget_view.addTab(self.tab_viewConfidence, "")
        self.tab_solvDef = QtWidgets.QWidget()
        self.tab_solvDef.setEnabled(True)
        self.tab_solvDef.setObjectName("tab_solvDef")
        self.label_viewSolDef = QtWidgets.QLabel(self.tab_solvDef)
        self.label_viewSolDef.setGeometry(QtCore.QRect(0, 0, 391, 391))
        self.label_viewSolDef.setMinimumSize(QtCore.QSize(320, 320))
        self.label_viewSolDef.setMaximumSize(QtCore.QSize(1000, 1000))
        self.label_viewSolDef.setFrameShape(QtWidgets.QFrame.Box)
        self.label_viewSolDef.setAlignment(QtCore.Qt.AlignCenter)
        self.label_viewSolDef.setEnabled(False)

        self.label_viewSolDef.setObjectName("label_viewSolDef")


        self.label_scaleAsSolDef = QtWidgets.QLabel(self.tab_solvDef)
        self.label_scaleAsSolDef.setText("Binarize scale as solvent def?")
        self.label_scaleAsSolDef.setStyleSheet("QLabel { color : red}")
        self.label_scaleAsSolDef.setGeometry(10,360,200,20)

        self.checkBox_scaleAsSolDef = QtWidgets.QCheckBox(self.tab_solvDef)
        self.checkBox_scaleAsSolDef.setEnabled(False)
        self.checkBox_scaleAsSolDef.setGeometry(220,360,20,20)
        self.slider_scaleAsSolDef = QtWidgets.QSlider(self.tab_solvDef)
        self.slider_scaleAsSolDef.setEnabled(False)
        self.slider_scaleAsSolDef.setGeometry(250,360,130,20)
        self.slider_scaleAsSolDef.setMinimum(1)
        self.slider_scaleAsSolDef.setMaximum(99)

        self.slider_scaleAsSolDef.setProperty("value", 20)
        self.slider_scaleAsSolDef.setSliderPosition(99)
        self.slider_scaleAsSolDef.setOrientation(QtCore.Qt.Horizontal)

        self.tabWidget_view.addTab(self.tab_solvDef, "")
        self.tab_viewModification = QtWidgets.QWidget()
        self.tab_viewModification.setEnabled(True)
        self.tab_viewModification.setObjectName("tab_viewModification")
        self.MplWidget_viewModification = MplWidget(self.tab_viewModification)
        self.MplWidget_viewModification.setGeometry(QtCore.QRect(0, 0, 391, 391))
        self.MplWidget_viewModification.setMinimumSize(QtCore.QSize(320, 320))
        self.MplWidget_viewModification.setMaximumSize(QtCore.QSize(400, 400))
        self.MplWidget_viewModification.setObjectName("MplWidget_viewModification")
        self.MplWidget_viewModification.setToolTip("Along the dashed line: \n"
                                                   "input = output (no change) \n\n"
                                                   "Modification above dashed line: \n"
                                                   "local pixel values amplified\n\n"
                                                   "Modification below dashed line: \n"
                                                   "local pixel values attenuated")

        self.tabWidget_view.addTab(self.tab_viewModification, "")
        self.tab_viewOutput = QtWidgets.QWidget()
        self.tab_viewOutput.setEnabled(True)
        self.tab_viewOutput.setObjectName("tab_viewOutput")


        self.label_viewOutput = QtWidgets.QLabel(self.tab_viewOutput)
        self.label_viewOutput.setGeometry(QtCore.QRect(0, 0, 391, 391))
        self.label_viewOutput.setMinimumSize(QtCore.QSize(320, 320))
        self.label_viewOutput.setMaximumSize(QtCore.QSize(1000, 1000))
        self.label_viewOutput.setFrameShape(QtWidgets.QFrame.Box)

        self.label_warnPreview = QtWidgets.QLabel(self.tab_viewOutput)
        self.label_warnPreview.setGeometry(QtCore.QRect(10, 330, 380, 60))
        self.label_warnPreview.setAlignment(QtCore.Qt.AlignCenter)
        whiteBold = QtGui.QFont()
        whiteBold.setBold(True)


        self.label_warnPreview.setFont(whiteBold)
        self.label_warnPreview.setStyleSheet("QLabel { color : white}")
        self.label_warnPreview.setText("This is very rough preview. \n Run occupy again to generate full-quality map")

        self.label_viewOutput.setAlignment(QtCore.Qt.AlignCenter)
        self.label_viewOutput.setEnabled(False)
        self.label_viewOutput.setObjectName("label_viewOutput")
        self.label_viewOutput.raise_()

        self.tabWidget_view.addTab(self.tab_viewOutput, "")
        self.tabWidget_output = QtWidgets.QTabWidget(MainWindow)
        self.tabWidget_output.setGeometry(QtCore.QRect(10, 640, 661, 171))
        self.tabWidget_output.setObjectName("tabWidget_output")
        self.tabWidget_output.setStyleSheet('''
        QTabWidget::tab-bar {
            alignment: left;
        }''')
        self.tab_log = QtWidgets.QWidget()
        self.tab_log.setObjectName("tab_log")
        self.gridLayoutWidget_8 = QtWidgets.QWidget(self.tab_log)
        self.gridLayoutWidget_8.setGeometry(QtCore.QRect(0, 0, 661, 141))
        self.gridLayoutWidget_8.setObjectName("gridLayoutWidget_8")
        self.gridLayout_log = QtWidgets.QGridLayout(self.gridLayoutWidget_8)
        self.gridLayout_log.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_log.setObjectName("gridLayout_log")
        self.textEdit_log = QtWidgets.QTextEdit(self.gridLayoutWidget_8)
        self.textEdit_log.setReadOnly(True)
        self.textEdit_log.setObjectName("textEdit_log")
        self.gridLayout_log.addWidget(self.textEdit_log, 0, 0, 1, 1)
        self.tabWidget_output.addTab(self.tab_log, "")

        self.tab_solventModel = QtWidgets.QWidget()
        self.tab_solventModel.setObjectName("tab_solventModel")

        self.label_solventModel = QtWidgets.QLabel(self.tab_solventModel)
        self.label_solventModel.setGeometry(QtCore.QRect(0, 0, 671, 141))
        self.label_solventModel.setMinimumSize(QtCore.QSize(320, 100))
        self.label_solventModel.setMaximumSize(QtCore.QSize(1000, 400))
        self.label_solventModel.setObjectName("label_solventModel")
        self.label_solventModel.setFrameShape(QtWidgets.QFrame.Box)
        self.label_solventModel.setAlignment(QtCore.Qt.AlignCenter)

        self.toolButton_expandSolModel=QtWidgets.QToolButton(self.label_solventModel)
        self.toolButton_expandSolModel.setGeometry(QtCore.QRect(580, 10, 70, 20))
        self.toolButton_expandSolModel.setText("Full view")
        self.toolButton_expandSolModel.setEnabled(False)

        self.tabWidget_output.addTab(self.tab_solventModel, "")
        self.gridLayoutWidget = QtWidgets.QWidget(MainWindow)
        self.gridLayoutWidget.setGeometry(QtCore.QRect(280, 495, 391, 31))
        self.gridLayoutWidget.setObjectName("gridLayoutWidget")
        self.gridLayout = QtWidgets.QGridLayout(self.gridLayoutWidget)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setObjectName("gridLayout")

        self.gridLayoutWidget_scaleAndDef = QtWidgets.QWidget(MainWindow)
        self.gridLayoutWidget_scaleAndDef.setGeometry(QtCore.QRect(280, 530, 391, 65))
        self.gridLayoutWidget_scaleAndDef.setObjectName("gridLayoutWidget")
        self.gridLayout_scaleAndDef = QtWidgets.QGridLayout(self.gridLayoutWidget_scaleAndDef)
        self.gridLayout_scaleAndDef.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_scaleAndDef.setObjectName("gridLayout")
        self.comboBox_inputScale = QtWidgets.QComboBox(self.gridLayoutWidget_scaleAndDef)
        self.comboBox_inputScale.setObjectName("comboBox_inputScale")
        self.gridLayout_scaleAndDef.addWidget(self.comboBox_inputScale, 0, 1, 1, 1)
        self.comboBox_inputSolventDef = QtWidgets.QComboBox(self.gridLayoutWidget_scaleAndDef)
        self.comboBox_inputSolventDef.setObjectName("comboBox_inputSoventDef")
        self.gridLayout_scaleAndDef.addWidget(self.comboBox_inputSolventDef, 1, 1, 1, 1)
        self.comboBox_inputSolventDef.addItem(" ")

        self.toolButton_inputScale_browse = QtWidgets.QToolButton(self.gridLayoutWidget_scaleAndDef)
        self.toolButton_inputScale_browse.setObjectName("toolButton_inputScale_browse")
        self.gridLayout_scaleAndDef.addWidget(self.toolButton_inputScale_browse, 0, 2, 1, 1)

        self.toolButton_inputSolventDef_browse = QtWidgets.QToolButton(self.gridLayoutWidget_scaleAndDef)
        self.toolButton_inputSolventDef_browse.setObjectName("toolButton_inputSolventDef_browse")
        self.gridLayout_scaleAndDef.addWidget(self.toolButton_inputSolventDef_browse, 1, 2, 1, 1)

        self.label_inputScale = QtWidgets.QLabel(self.gridLayoutWidget_scaleAndDef)
        self.label_inputScale.setEnabled(True)
        self.label_inputScale.setAlignment(QtCore.Qt.AlignRight)
        self.label_inputScale.setObjectName("label_inputScale")
        self.label_inputScale.setMaximumWidth(80)
        self.gridLayout_scaleAndDef.addWidget(self.label_inputScale,0,0,1,1)

        self.label_inputSolventDef = QtWidgets.QLabel(self.gridLayoutWidget_scaleAndDef)
        self.label_inputSolventDef.setEnabled(True)
        self.label_inputSolventDef.setAlignment(QtCore.Qt.AlignRight)
        self.label_inputSolventDef.setObjectName("label_inputSolventDef")
        self.label_inputSolventDef.setMaximumWidth(80)
        self.gridLayout_scaleAndDef.addWidget(self.label_inputSolventDef,1,0,1,1)

        self.spinBox_viewSlice = QtWidgets.QSpinBox(self.gridLayoutWidget)
        self.spinBox_viewSlice.setEnabled(True)
        self.spinBox_viewSlice.setMouseTracking(False)
        self.spinBox_viewSlice.setWrapping(False)
        self.spinBox_viewSlice.setFrame(True)
        self.spinBox_viewSlice.setReadOnly(False)
        self.spinBox_viewSlice.setKeyboardTracking(True)
        self.spinBox_viewSlice.setProperty("showGroupSeparator", False)
        self.spinBox_viewSlice.setMinimum(1)
        self.spinBox_viewSlice.setMaximum(128)
        self.spinBox_viewSlice.setSingleStep(1)
        self.spinBox_viewSlice.setStepType(QtWidgets.QAbstractSpinBox.DefaultStepType)
        self.spinBox_viewSlice.setProperty("value", 64)
        self.spinBox_viewSlice.setObjectName("spinBox_viewSlice")
        self.gridLayout.addWidget(self.spinBox_viewSlice, 0, 5, 1, 1)
        self.checkBox_viewX = QtWidgets.QCheckBox(self.gridLayoutWidget)
        self.checkBox_viewX.setChecked(True)
        self.checkBox_viewX.setObjectName("checkBox_viewX")
        self.gridLayout.addWidget(self.checkBox_viewX, 0, 0, 1, 1)
        self.checkBox_viewZ = QtWidgets.QCheckBox(self.gridLayoutWidget)
        self.checkBox_viewZ.setObjectName("checkBox_viewZ")
        self.gridLayout.addWidget(self.checkBox_viewZ, 0, 3, 1, 1)
        self.checkBox_viewY = QtWidgets.QCheckBox(self.gridLayoutWidget)
        self.checkBox_viewY.setObjectName("checkBox_viewY")
        self.gridLayout.addWidget(self.checkBox_viewY, 0, 2, 1, 1)
        self.horizontalSlider_viewSlice = QtWidgets.QSlider(self.gridLayoutWidget)
        self.horizontalSlider_viewSlice.setMinimum(1)
        self.horizontalSlider_viewSlice.setMaximum(128)
        self.horizontalSlider_viewSlice.setPageStep(1)
        self.horizontalSlider_viewSlice.setProperty("value", 64)
        self.horizontalSlider_viewSlice.setSliderPosition(64)
        self.horizontalSlider_viewSlice.setOrientation(QtCore.Qt.Horizontal)
        self.horizontalSlider_viewSlice.setObjectName("horizontalSlider_viewSlice")
        self.gridLayout.addWidget(self.horizontalSlider_viewSlice, 0, 4, 1, 1)
        self.gridLayoutWidget_2 = QtWidgets.QWidget(MainWindow)
        self.gridLayoutWidget_2.setGeometry(QtCore.QRect(10, 100, 261, 160))
        self.gridLayoutWidget_2.setObjectName("gridLayoutWidget_2")
        self.gridLayout_kernelOptions = QtWidgets.QGridLayout(self.gridLayoutWidget_2)
        self.gridLayout_kernelOptions.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_kernelOptions.setObjectName("gridLayout_kernelOptions")
        self.spinBox_kernelSize = QtWidgets.QSpinBox(self.gridLayoutWidget_2)
        self.spinBox_kernelSize.setEnabled(True)
        self.spinBox_kernelSize.setMouseTracking(False)
        self.spinBox_kernelSize.setWrapping(False)
        self.spinBox_kernelSize.setFrame(True)
        self.spinBox_kernelSize.setReadOnly(False)
        self.spinBox_kernelSize.setKeyboardTracking(True)
        self.spinBox_kernelSize.setProperty("showGroupSeparator", False)
        self.spinBox_kernelSize.setMinimum(3)
        self.spinBox_kernelSize.setMaximum(13)
        self.spinBox_kernelSize.setSingleStep(2)
        self.spinBox_kernelSize.setStepType(QtWidgets.QAbstractSpinBox.DefaultStepType)
        self.spinBox_kernelSize.setProperty("value", 3)
        self.spinBox_kernelSize.setObjectName("spinBox_kernelSize")
        self.gridLayout_kernelOptions.addWidget(self.spinBox_kernelSize, 2, 1, 1, 1)
        self.label_inputLowpass = QtWidgets.QLabel(self.gridLayoutWidget_2)
        self.label_inputLowpass.setEnabled(True)
        self.label_inputLowpass.setObjectName("label_inputLowpass")
        self.gridLayout_kernelOptions.addWidget(self.label_inputLowpass, 0, 0, 1, 1)
        self.label_tileSize = QtWidgets.QLabel(self.gridLayoutWidget_2)
        self.label_tileSize.setEnabled(True)
        self.label_tileSize.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
        self.label_tileSize.setObjectName("label_tileSize")
        self.gridLayout_kernelOptions.addWidget(self.label_tileSize, 5, 0, 1, 1)
        self.spinBox_tileSize = QtWidgets.QSpinBox(self.gridLayoutWidget_2)
        self.spinBox_tileSize.setEnabled(True)
        self.spinBox_tileSize.setMouseTracking(False)
        self.spinBox_tileSize.setWrapping(False)
        self.spinBox_tileSize.setFrame(True)
        self.spinBox_tileSize.setReadOnly(False)
        self.spinBox_tileSize.setKeyboardTracking(True)
        self.spinBox_tileSize.setProperty("showGroupSeparator", False)
        self.spinBox_tileSize.setMinimum(4)
        self.spinBox_tileSize.setMaximum(40)
        self.spinBox_tileSize.setSingleStep(2)
        self.spinBox_tileSize.setStepType(QtWidgets.QAbstractSpinBox.DefaultStepType)
        self.spinBox_tileSize.setProperty("value", 12)
        self.spinBox_tileSize.setObjectName("spinBox_tileSize")
        self.gridLayout_kernelOptions.addWidget(self.spinBox_tileSize, 5, 1, 1, 1)
        self.label_inputLowass_A = QtWidgets.QLabel(self.gridLayoutWidget_2)
        self.label_inputLowass_A.setEnabled(True)
        self.label_inputLowass_A.setObjectName("label_inputLowass_A")
        self.gridLayout_kernelOptions.addWidget(self.label_inputLowass_A, 0, 2, 1, 1)
        self.doubleSpinBox_kernelRadius = QtWidgets.QDoubleSpinBox(self.gridLayoutWidget_2)
        self.doubleSpinBox_kernelRadius.setEnabled(True)
        self.doubleSpinBox_kernelRadius.setMouseTracking(False)
        self.doubleSpinBox_kernelRadius.setWrapping(False)
        self.doubleSpinBox_kernelRadius.setFrame(True)
        self.doubleSpinBox_kernelRadius.setReadOnly(False)
        self.doubleSpinBox_kernelRadius.setKeyboardTracking(True)
        self.doubleSpinBox_kernelRadius.setProperty("showGroupSeparator", False)
        self.doubleSpinBox_kernelRadius.setObjectName("doubleSpinBox_kernelRadius")
        self.gridLayout_kernelOptions.addWidget(self.doubleSpinBox_kernelRadius, 1, 1, 1, 1)
        self.doubleSpinBox_Tau = QtWidgets.QDoubleSpinBox(self.gridLayoutWidget_2)
        self.doubleSpinBox_Tau.setEnabled(True)
        self.doubleSpinBox_Tau.setMouseTracking(False)
        self.doubleSpinBox_Tau.setWrapping(False)
        self.doubleSpinBox_Tau.setFrame(True)
        self.doubleSpinBox_Tau.setReadOnly(False)
        self.doubleSpinBox_Tau.setButtonSymbols(QtWidgets.QAbstractSpinBox.UpDownArrows)
        self.doubleSpinBox_Tau.setKeyboardTracking(True)
        self.doubleSpinBox_Tau.setProperty("showGroupSeparator", False)
        self.doubleSpinBox_Tau.setDecimals(2)
        self.doubleSpinBox_Tau.setMinimum(50.0)
        self.doubleSpinBox_Tau.setMaximum(99.9)
        self.doubleSpinBox_Tau.setSingleStep(0.1)
        self.doubleSpinBox_Tau.setProperty("value", 95.0)
        self.doubleSpinBox_Tau.setObjectName("doubleSpinBox_Tau")
        self.gridLayout_kernelOptions.addWidget(self.doubleSpinBox_Tau, 3, 1, 1, 1)
        self.label_kernelSize = QtWidgets.QLabel(self.gridLayoutWidget_2)
        self.label_kernelSize.setEnabled(True)
        self.label_kernelSize.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
        self.label_kernelSize.setObjectName("label_kernelSize")
        self.gridLayout_kernelOptions.addWidget(self.label_kernelSize, 2, 0, 1, 1)
        self.label_samplesValue = QtWidgets.QLabel(self.gridLayoutWidget_2)
        self.label_samplesValue.setObjectName("label_samplesValue")
        self.gridLayout_kernelOptions.addWidget(self.label_samplesValue, 4, 1, 1, 1)
        self.label_Tau_percent = QtWidgets.QLabel(self.gridLayoutWidget_2)
        self.label_Tau_percent.setEnabled(True)
        self.label_Tau_percent.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
        self.label_Tau_percent.setObjectName("label_Tau_percent")
        self.gridLayout_kernelOptions.addWidget(self.label_Tau_percent, 3, 2, 1, 1)
        self.label_kernelRadius_pix = QtWidgets.QLabel(self.gridLayoutWidget_2)
        self.label_kernelRadius_pix.setEnabled(True)
        self.label_kernelRadius_pix.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
        self.label_kernelRadius_pix.setObjectName("label_kernelRadius_pix")
        self.gridLayout_kernelOptions.addWidget(self.label_kernelRadius_pix, 2, 2, 1, 1)
        self.doubleSpinBox_inputLowpass = QtWidgets.QDoubleSpinBox(self.gridLayoutWidget_2)
        self.doubleSpinBox_inputLowpass.setEnabled(True)
        self.doubleSpinBox_inputLowpass.setDecimals(1)
        self.doubleSpinBox_inputLowpass.setMaximum(50.0)
        self.doubleSpinBox_inputLowpass.setSingleStep(1.0)
        self.doubleSpinBox_inputLowpass.setProperty("value", 0.0)
        self.doubleSpinBox_inputLowpass.setObjectName("doubleSpinBox_inputLowpass")
        self.gridLayout_kernelOptions.addWidget(self.doubleSpinBox_inputLowpass, 0, 1, 1, 1)
        self.label_samples = QtWidgets.QLabel(self.gridLayoutWidget_2)
        self.label_samples.setEnabled(True)
        self.label_samples.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
        self.label_samples.setObjectName("label_samples")
        self.gridLayout_kernelOptions.addWidget(self.label_samples, 4, 0, 1, 1)
        self.label_samples_voxels = QtWidgets.QLabel(self.gridLayoutWidget_2)
        self.label_samples_voxels.setEnabled(True)
        self.label_samples_voxels.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
        self.label_samples_voxels.setObjectName("label_samples_voxels")
        self.gridLayout_kernelOptions.addWidget(self.label_samples_voxels, 4, 2, 1, 1)
        self.label_kernelRadius = QtWidgets.QLabel(self.gridLayoutWidget_2)
        self.label_kernelRadius.setEnabled(True)
        self.label_kernelRadius.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
        self.label_kernelRadius.setObjectName("label_kernelRadius")
        self.gridLayout_kernelOptions.addWidget(self.label_kernelRadius, 1, 0, 1, 1)
        self.label_Tau = QtWidgets.QLabel(self.gridLayoutWidget_2)
        self.label_Tau.setEnabled(True)
        self.label_Tau.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
        self.label_Tau.setObjectName("label_Tau")
        self.gridLayout_kernelOptions.addWidget(self.label_Tau, 3, 0, 1, 1)
        self.label_kernelSize_pix = QtWidgets.QLabel(self.gridLayoutWidget_2)
        self.label_kernelSize_pix.setEnabled(True)
        self.label_kernelSize_pix.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
        self.label_kernelSize_pix.setObjectName("label_kernelSize_pix")
        self.gridLayout_kernelOptions.addWidget(self.label_kernelSize_pix, 1, 2, 1, 1)
        self.label_tileSize_pix = QtWidgets.QLabel(self.gridLayoutWidget_2)
        self.label_tileSize_pix.setEnabled(True)
        self.label_tileSize_pix.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
        self.label_tileSize_pix.setObjectName("label_tileSize_pix")
        self.gridLayout_kernelOptions.addWidget(self.label_tileSize_pix, 5, 2, 1, 1)

        self.gridLayoutWidget_6 = QtWidgets.QWidget(MainWindow)
        self.gridLayoutWidget_6.setGeometry(QtCore.QRect(10, 500, 261, 130))
        self.gridLayoutWidget_6.setObjectName("gridLayoutWidget_6")
        self.gridLayout_extraOptions = QtWidgets.QGridLayout(self.gridLayoutWidget_6)
        self.gridLayout_extraOptions.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_extraOptions.setObjectName("gridLayout_extraOptions")
        self.doubleSpinBox_outputLowpass = QtWidgets.QDoubleSpinBox(self.gridLayoutWidget_6)
        self.doubleSpinBox_outputLowpass.setEnabled(True)
        self.doubleSpinBox_outputLowpass.setDecimals(1)
        self.doubleSpinBox_outputLowpass.setMaximum(50.0)
        self.doubleSpinBox_outputLowpass.setSingleStep(1.0)
        self.doubleSpinBox_outputLowpass.setProperty("value", 8.0)
        self.doubleSpinBox_outputLowpass.setObjectName("doubleSpinBox_outputLowpass")
        self.gridLayout_extraOptions.addWidget(self.doubleSpinBox_outputLowpass, 1, 1, 1, 1)
        self.label_outputLowpass_A = QtWidgets.QLabel(self.gridLayoutWidget_6)
        self.label_outputLowpass_A.setEnabled(True)
        self.label_outputLowpass_A.setObjectName("label_outputLowpass_A")
        self.gridLayout_extraOptions.addWidget(self.label_outputLowpass_A, 1, 2, 1, 1)
        self.label_maxBox = QtWidgets.QLabel(self.gridLayoutWidget_6)
        self.label_maxBox.setEnabled(True)
        self.label_maxBox.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
        self.label_maxBox.setObjectName("label_maxBox")
        self.gridLayout_extraOptions.addWidget(self.label_maxBox, 0, 2, 1, 1)
        self.checkBox_histMatch = QtWidgets.QCheckBox(self.gridLayoutWidget_6)
        self.checkBox_histMatch.setToolTip("")
        self.checkBox_histMatch.setWhatsThis("")
        self.checkBox_histMatch.setTristate(False)
        self.checkBox_histMatch.setObjectName("checkBox_histMatch")
        self.gridLayout_extraOptions.addWidget(self.checkBox_histMatch, 4, 0, 1, 2)
        self.checkBox_S0 = QtWidgets.QCheckBox(self.gridLayoutWidget_6)
        self.checkBox_S0.setObjectName("checkBox_S0")
        self.gridLayout_extraOptions.addWidget(self.checkBox_S0, 3, 0, 1, 2)
        self.checkBox_suppresSolvent = QtWidgets.QCheckBox(self.gridLayoutWidget_6)
        self.checkBox_suppresSolvent.setObjectName("checkBox_suppresSolvent")
        self.gridLayout_extraOptions.addWidget(self.checkBox_suppresSolvent, 2, 0, 1, 1)
        self.spinBox_maxBox = QtWidgets.QSpinBox(self.gridLayoutWidget_6)
        self.spinBox_maxBox.setEnabled(True)
        self.spinBox_maxBox.setMouseTracking(False)
        self.spinBox_maxBox.setWrapping(False)
        self.spinBox_maxBox.setFrame(True)
        self.spinBox_maxBox.setReadOnly(False)
        self.spinBox_maxBox.setKeyboardTracking(True)
        self.spinBox_maxBox.setProperty("showGroupSeparator", False)
        self.spinBox_maxBox.setMinimum(128)
        self.spinBox_maxBox.setMaximum(1024)
        self.spinBox_maxBox.setSingleStep(32)
        self.spinBox_maxBox.setStepType(QtWidgets.QAbstractSpinBox.DefaultStepType)
        self.spinBox_maxBox.setProperty("value", 256)
        self.spinBox_maxBox.setObjectName("spinBox_maxBox")
        self.gridLayout_extraOptions.addWidget(self.spinBox_maxBox, 0, 1, 1, 1)
        self.checkBox_maxBox = QtWidgets.QCheckBox(self.gridLayoutWidget_6)
        self.checkBox_maxBox.setChecked(True)
        self.checkBox_maxBox.setObjectName("checkBox_maxBox")
        self.gridLayout_extraOptions.addWidget(self.checkBox_maxBox, 0, 0, 1, 1)
        self.checkBox_outputLowpass = QtWidgets.QCheckBox(self.gridLayoutWidget_6)
        self.checkBox_outputLowpass.setObjectName("checkBox_outputLowpass")
        self.gridLayout_extraOptions.addWidget(self.checkBox_outputLowpass, 1, 0, 1, 1)
        self.horizontalLayoutWidget_4 = QtWidgets.QWidget(MainWindow)
        self.horizontalLayoutWidget_4.setGeometry(QtCore.QRect(10, 430, 261, 25))
        self.horizontalLayoutWidget_4.setObjectName("horizontalLayoutWidget_4")
        self.horizontalLayout_scaleMode = QtWidgets.QHBoxLayout(self.horizontalLayoutWidget_4)
        self.horizontalLayout_scaleMode.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_scaleMode.setObjectName("horizontalLayout_scaleMode")
        self.checkBox_scaleOcc = QtWidgets.QCheckBox(self.horizontalLayoutWidget_4)
        self.checkBox_scaleOcc.setObjectName("checkBox_scaleOcc")
        self.horizontalLayout_scaleMode.addWidget(self.checkBox_scaleOcc)
        # self.label_slash = QtWidgets.QLabel(self.horizontalLayoutWidget_4)
        # self.label_slash.setEnabled(True)
        # self.label_slash.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
        # self.label_slash.setObjectName("label_slash")
        # self.horizontalLayout_scaleMode.addWidget(self.label_slash)
        self.checkBox_scaleRes = QtWidgets.QCheckBox(self.horizontalLayoutWidget_4)
        self.checkBox_scaleRes.setChecked(True)
        self.checkBox_scaleRes.setObjectName("checkBox_scaleRes")
        self.checkBox_scaleRes.hide()
        self.horizontalLayout_scaleMode.addWidget(self.checkBox_scaleRes)
        self.gridLayoutWidget_7 = QtWidgets.QWidget(MainWindow)
        self.gridLayoutWidget_7.setGeometry(QtCore.QRect(110, 520, 561, 80))
        self.gridLayoutWidget_7.setObjectName("gridLayoutWidget_7")
        self.gridLayout_extraInputMaps = QtWidgets.QGridLayout(self.gridLayoutWidget_7)
        self.gridLayout_extraInputMaps.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_extraInputMaps.setObjectName("gridLayout_extraInputMaps")

        self.toolButton_estimateScale = QtWidgets.QPushButton(MainWindow)
        self.toolButton_estimateScale.setEnabled(False)
        self.toolButton_estimateScale.setGeometry(QtCore.QRect(280, 600, 120, 64))
        #self.toolButton_run.setIcon(self.icon_small)
        self.toolButton_estimateScale.setIconSize(QtCore.QSize(56, 56))
        self.toolButton_estimateScale.setObjectName("toolButton_run")

        self.toolButton_modify = QtWidgets.QPushButton(MainWindow)
        self.toolButton_modify.setEnabled(False)
        self.toolButton_modify.setGeometry(QtCore.QRect(415, 600, 120, 64))
        #self.toolButton_run2.setIcon(self.icon_small)
        self.toolButton_modify.setIconSize(QtCore.QSize(56, 56))
        self.toolButton_modify.setObjectName("toolButton_run2")

        self.toolButton_chimerax = QtWidgets.QPushButton(MainWindow)
        self.toolButton_chimerax.setEnabled(False)
        self.toolButton_chimerax.setGeometry(QtCore.QRect(550, 600, 120, 64))
        #self.toolButton_chimerax.setIcon(self.icon_chimX)
        self.toolButton_chimerax.setIconSize(QtCore.QSize(56, 56))
        self.toolButton_chimerax.setObjectName("toolButton_chimerax")

        self.verticalLayoutWidget = QtWidgets.QWidget(MainWindow)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(10, 530, 91, 61))
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.verticalLayout_labelExtraInput = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout_labelExtraInput.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_labelExtraInput.setObjectName("verticalLayout_labelExtraInput")

        self.label_inputMap = QtWidgets.QLabel(MainWindow)
        self.label_inputMap.setEnabled(True)
        self.label_inputMap.setGeometry(QtCore.QRect(0, 30, 89, 31))

        self.label_inputMap.setAlignment(QtCore.Qt.AlignCenter)
        self.label_inputMap.setObjectName("label_inputMap")
        self.tabWidget_output.raise_()
        self.toolButton_chimerax.raise_()
        self.tabWidget_modification.raise_()
        self.tabWidget_view.raise_()
        self.gridLayoutWidget.raise_()
        self.gridLayoutWidget_2.raise_()
        self.gridLayoutWidget_7.raise_()
        self.toolButton_estimateScale.raise_()
        self.toolButton_modify.raise_()
        self.verticalLayoutWidget.raise_()
        self.label_inputMap.raise_()
        self.toolButton_expandSolModel.raise_()

        self.horizontalLayoutWidget.raise_()
        self.horizontalLayoutWidget_4.raise_()
        self.gridLayoutWidget_scaleAndDef.raise_()
        self.gridLayoutWidget_6.raise_()

        self.retranslateUi(MainWindow)
        self.tabWidget_modification.setCurrentIndex(0)
        self.tabWidget_view.setCurrentIndex(0)
        self.tabWidget_output.setCurrentIndex(0)

        # Mutually explusive options
        self.checkBox_scaleRes.clicked.connect(self.checkBox_scaleOcc.toggle)
        self.checkBox_scaleOcc.clicked.connect(self.checkBox_scaleRes.toggle)

        # Match viewPort slider and spinBox
        self.horizontalSlider_viewSlice.valueChanged['int'].connect(self.spinBox_viewSlice.setValue)
        self.spinBox_viewSlice.valueChanged['int'].connect(self.horizontalSlider_viewSlice.setValue)

        # Update viewport image on slice change
        self.spinBox_viewSlice.valueChanged['int'].connect(self.render_all_slices)

        # Render slice if tab is clicked
        self.tabWidget_view.tabBarClicked.connect(self.force_render_all_slices)

        # Update spinboxes when slider is moved
        self.horizontalSlider_amplPower.valueChanged['int'].connect(self.update_mod_spin_boxes)
        self.horizontalSlider_attnPower.valueChanged['int'].connect(self.update_mod_spin_boxes)
        self.horizontalSlider_sigmoidPower.valueChanged['int'].connect(self.update_mod_spin_boxes)
        self.horizontalSlider_sigmoidPivot.valueChanged['int'].connect(self.update_mod_spin_boxes)

        # Render plot if spinBoxes are changed
        self.doubleSpinBox_amplPower.valueChanged.connect(self.render_output_slice_with_focus)
        self.doubleSpinBox_attnPower.valueChanged.connect(self.render_output_slice_with_focus)
        self.doubleSpinBox_sigmoidPower.valueChanged.connect(self.render_output_slice_with_focus)
        self.doubleSpinBox_sigmoidPivot.valueChanged.connect(self.render_output_slice_with_focus)

        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 849, 22))
        self.menubar.setObjectName("menubar")

        self.menu_session = QtWidgets.QMenu("&Session",self.menubar)
        self.menu_session.setObjectName("menu_session")

        self.menu_Run = QtWidgets.QMenu("&Run",self.menubar)
        self.menu_Run.setObjectName("menu_Run")

        self.menu_help = QtWidgets.QMenu("&Help",self.menubar)
        self.menu_help.setObjectName("menu_help")

        MainWindow.setMenuBar(self.menubar)

        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.actiontutorial = QtWidgets.QAction("&Tutorial",MainWindow)
        self.actiontutorial.triggered.connect(self.tutorial_open)

        self.actionabout = QtWidgets.QAction("&About",MainWindow)
        self.actionabout.setObjectName("actionabout")
        self.actionabout.triggered.connect(self.window_about)

        self.actionhelpchimx = QtWidgets.QAction("&Locate chimeraX",MainWindow)
        self.actionhelpchimx.setObjectName("actionhelpchimx")
        self.actionhelpchimx.triggered.connect(self.chimx_open)

        self.actionchange_location = QtWidgets.QAction("&Set location",MainWindow)
        self.actionchange_location.setObjectName("actionchange_location")
        self.actionchange_location.triggered.connect(self.change_current_dir)
        self.actionclear_log = QtWidgets.QAction("&Clear log",MainWindow)
        self.actionclear_log.setObjectName("actionclear_log")
        self.actionclear_log.triggered.connect(self.clear_log)
        self.actionview_full_log = QtWidgets.QAction("&View full log",MainWindow)
        self.actionview_full_log.setObjectName("actionview_full_log")
        self.actionview_full_log.triggered.connect(self.view_full_log)


        self.action_verbose = QtWidgets.QAction("&Be verbose in log",MainWindow)
        self.action_verbose.setObjectName("action_verbose")
        self.action_verbose.setCheckable(True)

        self.action_print_command = QtWidgets.QAction("&Print command to log",MainWindow)
        self.action_print_command.setObjectName("action_print_command")
        self.action_print_command.triggered.connect(self.print_command)


        self.actionreset = QtWidgets.QAction("&Reset session",MainWindow)
        self.actionreset.setObjectName("actionreset")
        self.actionreset.triggered.connect(self.reset_session)


        self.actionestimateScale = QtWidgets.QAction("&Estimate scale",MainWindow)
        self.actionestimateScale.setObjectName("actionestimateScale")
        self.actionestimateScale.setEnabled(False)
        self.actionestimateScale.triggered.connect(self.estimate_scale)

        self.actionmodifyMap = QtWidgets.QAction("&Modify Map",MainWindow)
        self.actionmodifyMap.setObjectName("actionmodifyMap")
        self.actionmodifyMap.setEnabled(False)
        self.actionmodifyMap.triggered.connect(self.run_cmd)

        self.actionmakeSolDef = QtWidgets.QAction("&Generate solvent definition from scale",MainWindow)
        self.actionmakeSolDef.setObjectName("actionmakeSolDef")
        self.actionmakeSolDef.triggered.connect(self.generate_soldef_from_scale)
        self.actionmakeSolDef.setEnabled(False)

        self.actionmakeSubtractionMask = QtWidgets.QAction("Generate &subtraction mask",MainWindow)
        self.actionmakeSubtractionMask.setObjectName("actionsubtractionMask")
        self.actionmakeSubtractionMask.triggered.connect(self.generate_subtraction_mask)
        self.actionmakeSubtractionMask.setEnabled(False)


        self.menu_session.addAction(self.actionchange_location)
        self.menu_session.addAction(self.actionreset)
        self.menu_session.addSeparator()
        self.menu_session.addAction(self.actionclear_log)
        self.menu_session.addAction(self.actionview_full_log)
        self.menu_session.addSeparator()
        self.menu_session.addAction(self.action_verbose)
        self.menu_session.addAction(self.action_print_command)


        self.menu_Run.addAction(self.actionestimateScale)
        self.menu_Run.addAction(self.actionmodifyMap)
        self.menu_Run.addAction(self.actionmakeSolDef)
        self.menu_Run.addAction(self.actionmakeSubtractionMask)


        self.menu_help.addAction(self.actiontutorial)
        self.menu_help.addAction(self.actionabout)

        self.menubar.addAction(self.menu_session.menuAction())
        self.menubar.addAction(self.menu_Run.menuAction())
        self.menubar.addAction(self.menu_help.menuAction())

        self.detect_OS()
        self.have_chimerax()
        if self.chimerax_name is None:
            self.toolButton_chimerax.setText(f"  Launch\n  ChimeraX \n(not found)")
            self.toolButton_chimerax.setToolTip("Chimerax was not found, the \n"
                                                "OCCUPY_CHIMERAX environment \n"
                                                "variable can be set to \n"
                                                "point to your install location. \n\n "
                                                "more info through the help menu.")
            self.actionhelpchimx.setText("how to auto-detect chimeraX")
            self.menu_help.addAction(self.actionhelpchimx)

        else:
            self.toolButton_chimerax.setText(f"  Launch\n  ChimeraX")
            self.toolButton_chimerax.setToolTip("Run the chimerax command script \n"
                                                "to visualize the most recent  \n"
                                                "output from occupy.")

        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "OccuPy"))

        # Input Map
        self.toolButton_inputMap_browse.setText(_translate("MainWindow", "browse"))
        self.toolButton_inputMap_browse.clicked.connect(self.set_input_file)
        self.toolButton_inputMap_emdb.clicked.connect(self.fetch_emdb)
        self.toolButton_inputMap_emdb.setText(_translate("MainWindow", "emdb"))

        # Input scale Map
        self.toolButton_inputScale_browse.setText(_translate("MainWindow", "browse"))
        self.toolButton_inputScale_browse.clicked.connect(self.set_scale_file)

        # Input solvent Def
        self.toolButton_inputSolventDef_browse.setText(_translate("MainWindow", "browse"))
        self.toolButton_inputSolventDef_browse.clicked.connect(self.set_solvent_file)

        # Update when changing the input choice
        self.comboBox_inputMap.currentIndexChanged.connect(self.read_input_file)
        self.comboBox_inputScale.currentIndexChanged.connect(self.change_scale_file)
        self.comboBox_inputSolventDef.currentIndexChanged.connect(self.read_solvent_file)


        self.label_amplPower.setText(_translate("MainWindow", " Power"))
        self.tabWidget_modification.setTabText(self.tabWidget_modification.indexOf(self.tab_amplification), _translate("MainWindow", "Amplify"))

        self.label_attnPower.setText(_translate("MainWindow", " Power"))
        self.tabWidget_modification.setTabText(self.tabWidget_modification.indexOf(self.tab_attenuation), _translate("MainWindow", "Attenuate"))
        self.label_sigmoidPower.setText(_translate("MainWindow", " Power"))
        self.label_sigmoidPivot.setText(_translate("MainWindow", " Pivot"))
        self.tabWidget_modification.setTabText(self.tabWidget_modification.indexOf(self.tab_sigmoid), _translate("MainWindow", "Sigmoid"))

        self.tabWidget_modification.tabBarClicked.connect(self.toggle_scale_mode)
        self.groupBox_amplification.clicked.connect(self.toggle_scale_mode)
        self.groupBox_attenuation.clicked.connect(self.toggle_scale_mode)
        self.groupBox_sigmoid.clicked.connect(self.toggle_scale_mode)
        self.groupBox_amplification.clicked.connect(self.update_plot_params)
        self.groupBox_attenuation.clicked.connect(self.update_plot_params)
        self.groupBox_sigmoid.clicked.connect(self.update_plot_params)
        self.groupBox_amplification.clicked.connect(self.render_output_slice_with_focus)
        self.groupBox_attenuation.clicked.connect(self.render_output_slice_with_focus)
        self.groupBox_sigmoid.clicked.connect(self.render_output_slice_with_focus)

        self.checkBox_scaleAsSolDef.clicked.connect(self.update_scale_slider)
        self.slider_scaleAsSolDef.valueChanged.connect(self.update_scale_slider)

        self.tabWidget_view.setTabText(self.tabWidget_view.indexOf(self.tab_viewInput), _translate("MainWindow", "Input"))
        self.tabWidget_view.setTabText(self.tabWidget_view.indexOf(self.tab_viewScale), _translate("MainWindow", "Scale"))
        self.tabWidget_view.setTabText(self.tabWidget_view.indexOf(self.tab_viewConfidence), _translate("MainWindow", "Conf."))
        self.tabWidget_view.setTabText(self.tabWidget_view.indexOf(self.tab_solvDef), _translate("MainWindow", "Sol.def."))
        self.tabWidget_view.setTabText(self.tabWidget_view.indexOf(self.tab_viewModification), _translate("MainWindow", "Plot"))
        self.tabWidget_view.setTabText(self.tabWidget_view.indexOf(self.tab_viewOutput), _translate("MainWindow", "Preview"))
        self.textEdit_log.setPlaceholderText(_translate("MainWindow", "Output messages will go here...."))
        self.tabWidget_output.setTabText(self.tabWidget_output.indexOf(self.tab_log), _translate("MainWindow", "Output Log"))
        self.tabWidget_output.setTabText(self.tabWidget_output.indexOf(self.tab_solventModel), _translate("MainWindow", "Solvent model"))


        self.toolButton_chimerax.clicked.connect(self.run_chimerax)


        # Viewport X / Y / Z --------------------------------------
        self.checkBox_viewX.setText(_translate("MainWindow", "x"))
        self.checkBox_viewX.clicked.connect(self.view_x)
        self.checkBox_viewY.setText(_translate("MainWindow", "y"))
        self.checkBox_viewY.clicked.connect(self.view_y)
        self.checkBox_viewZ.setText(_translate("MainWindow", "z"))
        self.checkBox_viewZ.clicked.connect(self.view_z)


        # Kernel options
        self.label_inputLowpass.setText(_translate("MainWindow", "Input lowpass"))
        self.doubleSpinBox_inputLowpass.valueChanged.connect(self.set_kernel_radius)

        self.label_kernelRadius.setText(_translate("MainWindow", "Kernel radius"))
        self.doubleSpinBox_kernelRadius.valueChanged.connect(self.set_kernel_size)

        self.label_kernelSize.setText(_translate("MainWindow", "Kernel size"))
        self.spinBox_kernelSize.valueChanged.connect(self.set_kernel_tau)




        self.label_tileSize.setText(_translate("MainWindow", "Tile size"))
        self.label_inputLowass_A.setText(_translate("MainWindow", "Å"))

        self.set_default_views()


        # Kernel option labels
        self.label_samplesValue.setText(_translate("MainWindow", "-"))
        self.label_Tau_percent.setText(_translate("MainWindow", "%"))
        self.label_kernelRadius_pix.setText(_translate("MainWindow", "pixels"))
        self.label_samples.setText(_translate("MainWindow", "Samples"))
        self.label_samples_voxels.setText(_translate("MainWindow", "voxels"))
        self.label_Tau.setText(_translate("MainWindow", "Tau (percentile) "))
        self.label_kernelSize_pix.setText(_translate("MainWindow", "pixels"))
        self.label_tileSize_pix.setText(_translate("MainWindow", "pixels"))
        self.label_outputLowpass_A.setText(_translate("MainWindow", "Å"))
        self.label_maxBox.setText(_translate("MainWindow", "pix"))


        self.checkBox_histMatch.setText(_translate("MainWindow", "Histogram-match to input"))
        self.checkBox_S0.setText(_translate("MainWindow", "Naive normalization"))
        self.checkBox_suppresSolvent.setText(_translate("MainWindow", "Supress solvent"))
        self.checkBox_maxBox.setText(_translate("MainWindow", "Limit box size"))
        self.checkBox_outputLowpass.setText(_translate("MainWindow", "Output lowpass"))
        self.checkBox_scaleOcc.setText(_translate("MainWindow", "occupancy"))
        # self.label_slash.setText(_translate("MainWindow", "      or"))
        self.checkBox_scaleRes.setText(_translate("MainWindow", "resolution"))

        self.checkBox_histMatch.setToolTip(_translate("MainWindow", "When selected, the greyscale is matched\n"
                                                                    "against the input. This will may distort \n"
                                                                    "the continuity of the histogram. \n\n"
                                                                    "Expert/trial feature."))
        self.checkBox_S0.setToolTip(_translate("MainWindow", "When selected, the scale is normalized\n"
                                                             "against individual pixels at the selected\n"
                                                             "percentile. This makes the scale sensitive\n"
                                                             "to outliers and high pixel values, like \n"
                                                             "ions and high-mass object in high-res maps."))
        self.checkBox_suppresSolvent.setToolTip(_translate("MainWindow", "Mask the output by the confidence\n"
                                                                         "map shown in the conf tab of the viewer."))
        self.checkBox_maxBox.setToolTip(_translate("MainWindow", "Reduce the size of the map during scale estimation\n"
                                                                 "this cubic size. A smaller number reduces the time\n"
                                                                 "and memory required, at some resolution loss in the\n"
                                                                 "estimate."))
        self.checkBox_outputLowpass.setToolTip(_translate("MainWindow", "Limit the resolution of modified maps. \n"
                                                                        "This does not apply to scale maps."))
        self.checkBox_scaleOcc.setToolTip(_translate("MainWindow", "Use this mode to remove resolution-dependent\n"
                                                                   "contrast degradation, and approximately \n"
                                                                   "isolate contrast degradation due to occupancy.\n\n"
                                                                   "This is the mode used in map modification. "))
        self.checkBox_scaleRes.setToolTip(_translate("MainWindow", "Use this mode to estimate contrast degradation\n"
                                                                   "due to any factor, including flexibility and \n"
                                                                   "other sources of variable resolution, including \n"
                                                                   "occupancy.\n\n"
                                                                   "This mode cannot be used to modify maps."))



        self.toolButton_inputScale_browse.setText(_translate("MainWindow", "browse"))
        self.toolButton_inputScale_browse.setToolTip(_translate("MainWindow", "Load a scale map from file"))
        self.comboBox_inputScale.setToolTip(_translate("MainWindow", "The scale to display in the viewer \nand use for modification"))
        self.comboBox_inputSolventDef.setToolTip(_translate("MainWindow", "The solvent definition to display \n"
                                                                          "in the viewer and use for modification\n\n"
                                                                          "Note that you can leave deselect it."))
        self.toolButton_inputSolventDef_browse.setText(_translate("MainWindow", "browse"))
        self.toolButton_inputSolventDef_browse.setToolTip(_translate("MainWindow", "Load a solvent definition from file"))
        self.toolButton_estimateScale.setText(_translate("MainWindow", "  Estimate  \n  scale  "))#ɒk.jə.paɪ"))
        self.toolButton_estimateScale.setToolTip(_translate("MainWindow", "Estimate the scale of the selected input map."))
        self.toolButton_estimateScale.clicked.connect(self.estimate_scale)
        self.toolButton_modify.setText(_translate("MainWindow", "  Modify  \n  Map  "))
        self.toolButton_modify.setToolTip(_translate("MainWindow", "Perform ALL enabled modifications"))
        self.toolButton_modify.clicked.connect(self.run_cmd)
        self.label_inputScale.setText(_translate("MainWindow", "  scale map"))
        self.label_inputSolventDef.setText(_translate("MainWindow", " solvent def"))
        self.label_inputMap.setText(_translate("MainWindow", "  Input map"))

        self.toolButton_expandSolModel.clicked.connect(self.window_solvent_model)

        self.tabWidget_output.tabBarDoubleClicked.connect(self.view_full_log)


    def tutorial_open(self):
        import webbrowser
        url = "https://occupy.readthedocs.io/en/latest/Tutorials/intro/"
        webbrowser.open(url, new=0, autoraise=True)

    def chimx_open(self):
        import webbrowser
        url = "https://occupy.readthedocs.io/en/latest/Troubleshooting/chimX_trbl/"
        webbrowser.open(url, new=0, autoraise=True)

    def update_scale_slider(self):

        self.label_viewSolDef.clear()
        if self.checkBox_scaleAsSolDef.isChecked():
            self.slider_scaleAsSolDef.setEnabled(True)
            self.render_solvent_slice()
        else:
            self.slider_scaleAsSolDef.setEnabled(False)
            self.render_solvent_slice()



    def set_default_views(self):
        self.label_viewInput.setText("Load an input file (.map/.mrc)")
        self.label_viewScale.setText("Run occupy or \n load a scale (.map/.mrc)")
        self.label_viewConfidence.setText("Confidence is dependent on a \n "
                                        "solvent model, and is  shown when \n "
                                        "occupy has been run.")
        self.label_viewSolDef.setText("Provide a solvent definition (.map/.mrc) \n "
                                      "to help contruct a solvent model. You can \n "
                                      "provide a conventional solvent mask, but \n"
                                      "occupy will not use it to mask.  \n\n"
                                      "A solvent definition is optional input.")
        self.label_viewOutput.setText("This is a preview of the modification \n"
                                      "by the chosen scale. \n\n"
                                      "To view a preview, you need \n "
                                      "to have selected both \n"
                                      "  1) an input map       &   \n"
                                      "  2) an estimated scale  \n\n"
                                      "The loaded scale must be \n"
                                      "an occupancy-based scale. \n\n"
                                      "The preview is rough, you will have to \n"
                                      "run occupy to get accurate modification \n"
                                      "maps written to disk.")
        self.label_solventModel.setText("Run occupy to \n view the solvent model")

    def generate_subtraction_mask(self):

        N=1000
        scale_file_name = self.comboBox_inputScale.currentText()

        if len(scale_file_name)>3:

            did_something = False

            scale_data = mf.mmap(scale_file_name)
            scale_index = (scale_data.data*(N-1)).astype(np.int16)

            if self.groupBox_attenuation.isChecked() and self.MplWidget_viewModification.attenuation_power > 1:
                x = np.linspace(0, 1, N)
                s_attn = x ** (self.MplWidget_viewModification.attenuation_power-1)

                s_attn =np.clip(s_attn,0,1)

                sub_mask_attn = s_attn[scale_index]
                sub_mask_attn_name = f'subtraction_mask_attn_' \
                                     f'{self.MplWidget_viewModification.attenuation_power}.' \
                                     f'mrc'
                #TODO wrong size, resample to input map size
                map_tools.new_mrc(sub_mask_attn, sub_mask_attn_name, parent=scale_file_name)

                did_something=True
                self.occupy_log(f'Made {sub_mask_attn_name}')


            if self.groupBox_sigmoid.isChecked() and self.MplWidget_viewModification.sigmoid_power > 1:
                x, s_sigm = occupancy.scale_mapping_sigmoid(self.MplWidget_viewModification.sigmoid_pivot,
                                                        self.MplWidget_viewModification.sigmoid_power, n=N)

                # No amplification permitted during subtraction, limit sigmoid above pivot
                n_pivot = int(N * self.MplWidget_viewModification.sigmoid_pivot)
                s_sigm[n_pivot:] = 1
                s_sigm[0]=0

                s_sigm[1:n_pivot] = np.divide(s_sigm[1:n_pivot], x[1:n_pivot])
                s_sigm = np.clip(s_sigm,0,1)

                sub_mask_sigm = s_sigm[scale_index]
                sub_mask_sigm_name = f'subtraction_mask_sigm_' \
                                     f'{self.MplWidget_viewModification.sigmoid_pivot}.' \
                                     f'{self.MplWidget_viewModification.sigmoid_power}.' \
                                     f'mrc'
                map_tools.new_mrc(sub_mask_sigm,sub_mask_sigm_name, parent=scale_file_name)

                did_something = True
                self.occupy_log(f'Made {sub_mask_sigm_name}')

            scale_data.close()
            if not did_something:
                self.occupy_log("No subtraction mask generated, because neither attenuation nor sigmoid modification \
                with power > 1 was active.")
        else:
            self.occupy_log("No subtraction mask generated, because no scale was provided.")

    def reset_session(self):
        # Remove input files
        self.comboBox_inputMap.clear()
        self.comboBox_inputScale.clear()
        self.confidence_file_name = None

        self.comboBox_inputSolventDef.clear()
        self.comboBox_inputSolventDef.addItem(" ")

        # Inactive Buttons
        self.toolButton_estimateScale.setEnabled(False)
        self.actionestimateScale.setEnabled(self.toolButton_estimateScale.isEnabled())

        self.update_can_modify()

        self.toolButton_chimerax.setEnabled(False)
        self.checkBox_scaleAsSolDef.setChecked(False)
        self.checkBox_scaleAsSolDef.setEnabled(False)
        self.actionmakeSolDef.setEnabled(False)

        # Should clear all views
        self.set_default_views()

        # Clear output displays
        self.textEdit_log.clear()

        self.new_session = True

    def fetch_emdb(self):

        self.Dialog_emdb = EMDB_dialog()
        self.Dialog_emdb.make_dialog()
        self.Dialog_emdb.exec()

        id = self.Dialog_emdb.id

        if id is None or id == 0:
            pass
        else:
            self.occupy_log(f'Fetching emdb {id}...')
            map_name = ''
            with Capturing() as output:
                map_name = map_tools.fetch_EMDB(id)

            for i in output:
                self.occupy_log(i,save=False)

            if map_name is not None:

                self.add_input_file(str(map_name))


    def set_input_file(self):
        import os

        # Open dialog to choose file
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(None, "Select Image", os.getcwd(),
                                                            "Image Files (*.mrc *.map);;All Files (*)")  # Ask for file

        if file_name:
            self.label_viewInput.setEnabled(True)
            idx = None
            new_file = True
            for i in range(self.comboBox_inputMap.count()):
                if self.comboBox_inputMap.itemText(i) == file_name:
                    idx = i
                    new_file = False

            if new_file:

                scale_mode = self.check_scale_mode(file_name)
                if scale_mode is not None:
                    self.occupy_warn(f'{file_name} appears to be a scale file, '
                                     f'you should not use this as input.')
                    return


                self.comboBox_inputMap.addItem(file_name)
                n = self.comboBox_inputMap.count()
                self.comboBox_inputMap.setCurrentIndex(n-1)

                self.read_input_file()

                self.toolButton_estimateScale.setEnabled(True)
                self.actionestimateScale.setEnabled(self.toolButton_estimateScale.isEnabled())
                self.toolButton_estimateScale.clearFocus()
                self.occupy_log(f'Opened {file_name}')
            else:
                self.comboBox_inputMap.setCurrentIndex(idx)
                self.occupy_log(f'File {file_name} already open')
        elif len(file_name)>3:
            self.occupy_log(f'File {file_name} not found')


    def add_input_file(self,new_input_file):
        if new_input_file:
            new_file = True
            idx = None
            for i in range(self.comboBox_inputMap.count()):
                if self.comboBox_inputMap.itemText(i) == new_input_file:
                    idx = i
                    new_file = False
        if new_file:
            self.comboBox_inputMap.addItem(str(new_input_file))
            n = self.comboBox_inputMap.count()
            self.comboBox_inputMap.setCurrentIndex(n - 1)
        else:
            self.comboBox_inputMap.setCurrentIndex(idx)

        self.read_input_file()

    def read_input_file(self):
        #TODO check that file/map still exists

        # Get file name or object
        file_name = self.comboBox_inputMap.currentText()

        if file_name != '':
            # Open memory mapped to set options etc.
            f = mf.mmap(file_name)

            # Slider and spinbox in view window
            n = f.header['nx']

            ny = f.header['ny']
            nz = f.header['nz']


            # Only permit cubic
            if n == ny == nz:

                self.infile_minval = np.min(f.data)
                self.infile_maxval = np.max(f.data)
                self.infile_size = n

                self.spinBox_viewSlice.setMaximum(n)
                self.spinBox_viewSlice.setValue(n//2)

                self.horizontalSlider_viewSlice.setRange(1, n)
                self.horizontalSlider_viewSlice.setValue(n//2)

                # Fill view pane
                self.render_input_slice()

                # TODO compute kernel options
                self.set_lowpass()

            else:

                self.occupy_log('Input is not cubic.')


            self.label_viewInput.setEnabled(True)
            self.toolButton_estimateScale.setEnabled(True)
            self.actionestimateScale.setEnabled(self.toolButton_estimateScale.isEnabled())

            # Close the file
            f.close()

            self.tabWidget_view.setCurrentIndex(self.tabWidget_view.indexOf(self.tab_viewInput))
            self.render_input_slice()

    def render_input_slice(self,force=False):

        # Check if input view is active (currently viewed)
        # We don't want to read and render a slice that we're not viewing
        if self.tabWidget_view.currentIndex() == self.tabWidget_view.indexOf(self.tab_viewInput) or force:

            # Get file name or object
            file_name = self.comboBox_inputMap.currentText()

            # Get file slice number
            slice = self.horizontalSlider_viewSlice.value()

            # If there is something to render
            if file_name:
                # Open memory-mapped (much faster than open)
                f = mf.mmap(file_name)

                # Get the dimensions (assume cubic based in read-check)
                n = int(f.header['nx'])

                # Safe-guards
                if not slice or slice > n:
                    slice = n//2

                # Render the selected dimension
                if self.checkBox_viewX.isChecked():
                    t = f.data[slice-1,:,:]
                elif self.checkBox_viewY.isChecked():
                    t = f.data[:,slice-1,:]
                elif self.checkBox_viewZ.isChecked():
                    t = f.data[:, :, slice-1]

                # Grayscale normalization
                t = (t-self.infile_minval)/(self.infile_maxval-self.infile_minval)

                # Construct and render image
                im_data = np.copy(np.array((t*255).astype(np.uint8)))
                # get the shape of the array
                height, width = np.shape(im_data)

                # calculate the total number of bytes in the frame
                totalBytes = im_data.nbytes

                # divide by the number of rows
                bytesPerLine = int(totalBytes / height)

                qimage = QtGui.QImage(im_data,n,n,bytesPerLine,QtGui.QImage.Format_Grayscale8)# Setup pixmap with the provided image
                pixmap = QtGui.QPixmap(qimage) # Setup pixmap with the provided image
                pixmap = pixmap.scaled(self.label_viewInput.width(), self.label_viewInput.height(), QtCore.Qt.KeepAspectRatio) # Scale pixmap
                self.label_viewInput.setPixmap(pixmap) # Set the pixmap onto the label
                self.label_viewInput.setAlignment(QtCore.Qt.AlignCenter) # Align the label to center
                del im_data
                f.close()

    def check_scale_mode(self,file_name):

        occ_mode = None

        if file_name != '':
            #Label method
            f = mf.mmap(file_name)

            not_found = True
            nlabl = f.header['nlabl']
            for i in np.arange(nlabl):
                label = str(f.header['label'][i])
                if "occupy scale: occ" in label:
                    occ_mode = 'occ'
                    not_found = False
                    break
                elif "occupy scale: res" in label:
                    occ_mode = 'res'
                    not_found = False
                    break

            #Keep this alive for now, but it hsould be safe to delete to make it more difficult tho cheat
            if not_found:
                # String method as fallback
                if "scale_occ_" in file_name:
                    occ_mode = 'occ'
                elif "scale_res_" in file_name:
                    occ_mode = 'res'

            if not_found and nlabl == 10:
                occ_mode = 'full'

        return occ_mode

    def set_scale_mode(self,scale_file_name):

        self.occ_scale = False
        self.res_scale = False

        scale_mode = self.check_scale_mode(scale_file_name)
        if scale_mode == 'occ':
            self.occ_scale = True
        elif scale_mode == 'res':
            self.res_scale = True
        elif scale_mode =='full':
            print("There was nothing to confirm this is an occ scale, but all labels are full, so permitting.")
            self.occ_scale = True
        else:
            self.occupy_log('Could not find scale mode during scale file load')


    def change_input_file(self):
        self.in_file_name = str(self.comboBox_inputMap.currentText())
        self.render_input_slice()
        self.render_output_slice()

    def change_scale_file(self):
        self.scale_file_name = str(self.comboBox_inputScale.currentText())
        self.set_scale_mode(self.scale_file_name)
        self.render_scale_slice()
        self.render_output_slice()

    def set_scale_file(self):
        import os
        scale_file_name, _ = QtWidgets.QFileDialog.getOpenFileName(None, "Select Image", os.getcwd(),
                                                                  "Image Files (*.mrc *.map);;All Files (*)")  # Ask for file
        if scale_file_name:
            new_file = True
            idx = None
            for i in range(self.comboBox_inputScale.count()):
                if self.comboBox_inputScale.itemText(i) == scale_file_name:
                    idx = i
                    new_file = False
            if new_file:
                self.label_viewScale.setEnabled(True)
                self.scale_file_name = str(scale_file_name)
                self.set_scale_mode(self.scale_file_name)

                self.comboBox_inputScale.addItem(str(self.scale_file_name))
                n = self.comboBox_inputScale.count()
                self.comboBox_inputScale.setCurrentIndex(n-1)
            else:
                self.comboBox_inputScale.setCurrentIndex(idx)

            self.read_scale_file()
            self.checkBox_scaleAsSolDef.setEnabled(True)


    def add_scale_file(self,new_scale_file):
        self.checkBox_scaleAsSolDef.setEnabled(True)

        self.scale_file_name = str(new_scale_file)
        self.set_scale_mode(self.scale_file_name)

        if new_scale_file:
            new_file = True
            idx = None
            for i in range(self.comboBox_inputScale.count()):
                if self.comboBox_inputScale.itemText(i) == new_scale_file:
                    idx = i
                    new_file = False
        if new_file:
            self.comboBox_inputScale.addItem(str(self.scale_file_name))
            n = self.comboBox_inputScale.count()
            self.comboBox_inputScale.setCurrentIndex(n - 1)
        else:
            self.comboBox_inputScale.setCurrentIndex(idx)

        self.read_scale_file()


    def read_scale_file(self):
        #TODO check that file/map still exists

        # Get file name or object
        scale_file_name = self.comboBox_inputScale.currentText()

        if scale_file_name:

            # Open memory mapped to set options etc.
            f = mf.mmap(scale_file_name)

            # Slider and spinbox in view window
            n = f.header['nx']

            ny = f.header['ny']
            nz = f.header['nz']

            # Only permit cubic
            if n == ny == nz:

                # Fill view pane
                self.render_scale_slice()

            else:

                self.occupy_log('Scale input is not cubic.')

            # Close the file
            f.close()


    def render_scale_slice(self,force=False):

        # Check if input view is active (currently viewed)
        # We don't want to read and render a slice that we're not viewing
        if self.tabWidget_view.currentIndex() == self.tabWidget_view.indexOf(self.tab_viewScale) or force:

            # Get file name or object
            scale_file_name = self.comboBox_inputScale.currentText()

            # Get file slice number
            slice = self.horizontalSlider_viewSlice.value()


            # If there is something to render
            if scale_file_name:
                self.label_viewScale.setEnabled(True)

                # Open memory-scale_file_name (much faster than open)
                f = mf.mmap(scale_file_name)
                # Get the dimensions (assume cubic based in read-check)
                n = f.header['nx']

                # Let the input map decide the slice number if the scale is on another grid
                input_file_name = self.comboBox_inputMap.currentText()
                if input_file_name:
                    # Open memory-scale_file_name (much faster than open)
                    f_input = mf.mmap(input_file_name)
                    # Get the dimensions (assume cubic based in read-check)
                    n_input = f_input.header['nx']

                    if n != n_input:
                        # The equivalent slice in the scale image
                        slice = int((slice / float(n_input)) * n)

                    f_input.close()

                #self.horizontalSlider_viewSlice.setRange(1, n)
                #self.spinBox_viewSlice.setMaximum(n)

                # Safe-guards
                if slice < 0 or slice > n:
                    slice = n//2

                # Render the selected dimension
                if self.checkBox_viewX.isChecked():
                    t = f.data[slice-1,:,:]
                elif self.checkBox_viewY.isChecked():
                    t = f.data[:,slice-1,:]
                elif self.checkBox_viewZ.isChecked():
                    t = f.data[:, :, slice-1]

                # Grayscale normalization
                #tmin = f.header['dmin']
                #tmax = f.header['dmax']
                #t = (t-tmin)/(tmax-tmin)

                # Construct and render image
                im_data = np.array((t*255).astype(np.uint8))
                qimage = QtGui.QImage(im_data,n,n,QtGui.QImage.Format_Grayscale8)# Setup pixmap with the provided image
                pixmap = QtGui.QPixmap(qimage) # Setup pixmap with the provided image
                pixmap = pixmap.scaled(self.label_viewScale.width(), self.label_viewScale.height(), QtCore.Qt.KeepAspectRatio) # Scale pixmap
                self.label_viewScale.setPixmap(pixmap) # Set the pixmap onto the label
                self.label_viewScale.setAlignment(QtCore.Qt.AlignCenter) # Align the label to center

                f.close()

        # Just trigger GUI possibilities
        else:
            self.update_plot_params()

    def set_solvent_file(self,solvent_file_name=None,generate=False):
        import os
        if solvent_file_name is None or solvent_file_name is False:
            solvent_file_name, _ = QtWidgets.QFileDialog.getOpenFileName(None, "Select Image", os.getcwd(),
                                                                   "Image Files (*.mrc *.map);;All Files (*)")  # Ask for file
        new_file = True
        idx = None
        for i in range(self.comboBox_inputSolventDef.count()):
            if self.comboBox_inputSolventDef.itemText(i) == solvent_file_name:
                idx = i
                new_file = False

        if new_file:
            if solvent_file_name:
                self.label_viewSolDef.setEnabled(True)
                # TODO loop and set if new, otherwise change active
                self.comboBox_inputSolventDef.addItem(str(solvent_file_name))
                n = self.comboBox_inputSolventDef.count()
                self.comboBox_inputSolventDef.setCurrentIndex(n-1)

                # only read if its a browsed input
                if not generate:
                    self.read_solvent_file()

    def read_solvent_file(self):
        # TODO check that file/map still exists

        # Get file name or object
        solvent_file_name = self.comboBox_inputSolventDef.currentText()

        if len(solvent_file_name)>3:

            # Open memory mapped to set options etc.
            f = mf.mmap(solvent_file_name)

            # Slider and spinbox in view window
            n = f.header['nx']

            ny = f.header['ny']
            nz = f.header['nz']

            # Only permit cubic
            if n == ny == nz:

                # Fill view pane
                self.render_solvent_slice()

            else:

                self.occupy_log('Solvent definition input is not cubic.')

            # Close the file
            f.close()
        else:
            self.label_viewSolDef.clear()
            self.checkBox_scaleAsSolDef.setChecked(False)
            self.slider_scaleAsSolDef.setEnabled(False)

    def render_solvent_slice(self,force=False):
        self.label_viewSolDef.setEnabled(True)
        # Check if input view is active (currently viewed)
        # We don't want to read and render a slice that we're not viewing
        if self.tabWidget_view.currentIndex() == self.tabWidget_view.indexOf(self.tab_solvDef) or force:

            solvent_file_name = ''
            threshold = None

            #Use the scale to render
            if self.checkBox_scaleAsSolDef.isChecked():
                # Get file name or object
                solvent_file_name = self.comboBox_inputScale.currentText()
                threshold = int( 255 * float(self.slider_scaleAsSolDef.value()) / 100.0 )
            else:
                self.label_viewSolDef.clear()

                # Get file name or object
                solvent_file_name = self.comboBox_inputSolventDef.currentText()

            # Get file slice number
            slice = self.horizontalSlider_viewSlice.value()

            # If there is something to render
            if len(solvent_file_name) > 3:

                # Open memory-solvent_file_name (much faster than open)
                f = mf.mmap(solvent_file_name)
                # Get the dimensions (assume cubic based in read-check)
                n = f.header['nx']

                # Let the input map decide the slice number if the solvent is on another grid
                input_file_name = self.comboBox_inputMap.currentText()
                if input_file_name:
                    # Open memory-mapped (much faster than open)
                    f_input = mf.mmap(input_file_name)
                    # Get the dimensions (assume cubic based in read-check)
                    n_input = f_input.header['nx']

                    if n != n_input:
                        # The equivalent slice in the possibly
                        slice = int((slice / float(n_input)) * n)

                    f_input.close()



                # Safe-guards
                if not slice or slice > n:
                    slice = n // 2

                # Render the selected dimension
                if self.checkBox_viewX.isChecked():
                    t = f.data[slice - 1, :, :]
                elif self.checkBox_viewY.isChecked():
                    t = f.data[:, slice - 1, :]
                elif self.checkBox_viewZ.isChecked():
                    t = f.data[:, :, slice - 1]

                # Grayscale normalization
                # tmin = f.header['dmin']
                # tmax = f.header['dmax']
                # t = (t-tmin)/(tmax-tmin)

                # Construct and render image
                im_data = np.array((t * 255).astype(np.uint8))

                if threshold is not None:
                    self.actionmakeSolDef.setEnabled(True)
                    im_data = np.array((im_data > threshold).astype(np.uint8))*255
                else:

                    self.actionmakeSolDef.setEnabled(False)

                qimage = QtGui.QImage(im_data, n, n,
                                      QtGui.QImage.Format_Grayscale8)  # Setup pixmap with the provided image
                pixmap = QtGui.QPixmap(qimage)  # Setup pixmap with the provided image
                pixmap = pixmap.scaled(self.label_viewSolDef.width(), self.label_viewSolDef.height(),
                                       QtCore.Qt.KeepAspectRatio)  # Scale pixmap
                self.label_viewSolDef.setPixmap(pixmap)  # Set the pixmap onto the label
                self.label_viewSolDef.setAlignment(QtCore.Qt.AlignCenter)  # Align the label to center

                f.close()

    def render_confidence_slice(self,force=False):

        # Check if input view is active (currently viewed)
        # We don't want to read and render a slice that we're not viewing
        if self.tabWidget_view.currentIndex() == self.tabWidget_view.indexOf(self.tab_viewConfidence) or force:
            if self.confidence_file_name:
                self.label_viewConfidence.setEnabled(True)

                # Get file name or object
                confidence_file_name = self.confidence_file_name

                # Get file slice number
                slice = self.horizontalSlider_viewSlice.value()

                # If there is something to render
                if confidence_file_name is not None:

                    # Open memory-solvent_file_name (much faster than open)
                    f = mf.mmap(confidence_file_name)
                    # Get the dimensions (assume cubic based in read-check)
                    n = f.header['nx']

                    # Let the input map decide the slice number if the confidence is on another grid
                    input_file_name = self.comboBox_inputMap.currentText()
                    if input_file_name:
                        # Open memory-mapped (much faster than open)
                        f_input = mf.mmap(input_file_name)
                        # Get the dimensions (assume cubic based in read-check)
                        n_input = f_input.header['nx']

                        if n != n_input:
                            # The equivalent slice in the possibly
                            slice = int((slice / float(n_input)) * n)

                        f_input.close()
                    else:
                        self.horizontalSlider_viewSlice.setRange(1, n)

                        self.spinBox_viewSlice.setMaximum(n)

                    # Safe-guards
                    if not slice or slice > n:
                        slice = n // 2

                    # Render the selected dimension
                    if self.checkBox_viewX.isChecked():
                        t = f.data[slice - 1, :, :]
                    elif self.checkBox_viewY.isChecked():
                        t = f.data[:, slice - 1, :]
                    elif self.checkBox_viewZ.isChecked():
                        t = f.data[:, :, slice - 1]

                    # Grayscale normalization
                    # tmin = f.header['dmin']
                    # tmax = f.header['dmax']
                    # t = (t-tmin)/(tmax-tmin)

                    # Construct and render image
                    im_data = np.array((t * 255).astype(np.uint8))
                    qimage = QtGui.QImage(im_data, n, n,
                                          QtGui.QImage.Format_Grayscale8)  # Setup pixmap with the provided image
                    pixmap = QtGui.QPixmap(qimage)  # Setup pixmap with the provided image
                    pixmap = pixmap.scaled(self.label_viewConfidence.width(), self.label_viewConfidence.height(),
                                           QtCore.Qt.KeepAspectRatio)  # Scale pixmap
                    self.label_viewConfidence.setPixmap(pixmap)  # Set the pixmap onto the label
                    self.label_viewConfidence.setAlignment(QtCore.Qt.AlignCenter)  # Align the label to center

                    f.close()
            else:
                self.label_viewConfidence.setEnabled(False)


    def render_all_slices(self):
        self.render_input_slice()
        self.render_scale_slice()
        self.render_solvent_slice()
        self.render_output_slice()
        if self.confidence_file_name is not None:
            self.render_confidence_slice()

    def force_render_all_slices(self):
        self.render_input_slice(force=True)
        self.render_scale_slice(force=True)
        self.render_solvent_slice(force=True)
        self.render_output_slice(force=True)
        if self.confidence_file_name is not None:
            self.render_confidence_slice(force=True)

    def set_lowpass(self):
        # Get file name or object
        file_name = self.comboBox_inputMap.currentText()

        # If there is something to work with
        if file_name:

            # Open memory-mapped (much faster than open)
            f = mf.mmap(file_name)

            # Get the dimensions (assume cubic based in read-check)
            n = f.header['nx']

            # Get voxel size
            self.inputMap.voxel_size_ori = self.inputMap.voxel_size_proc = f.voxel_size.x
            max_box = self.spinBox_maxBox.value()

            downscale_processing = n > max_box
            if downscale_processing:
                n_proc = np.min([n,max_box])
                self.inputMap.voxel_size_ori = self.inputMap.voxel_size_proc * n/np.float(n_proc)

            lower_limit_default = 3 * self.inputMap.voxel_size_proc
            self.inputMap.lowpass = np.max([lower_limit_default,8.0])

            # Set gui
            self.doubleSpinBox_inputLowpass.setValue(self.inputMap.lowpass)

            # Propagate to other settings
            self.set_kernel_size()

    def set_kernel_radius(self):
        self.inputMap.lowpass = self.doubleSpinBox_inputLowpass.value()
        old_kernel_radius = self.inputMap.kernel_radius

        # Make a kernel (morphological structuring element) for max-filter (greyscale dilation).
        self.inputMap.kernel_radius = self.doubleSpinBox_inputLowpass.value() / (2 * self.inputMap.voxel_size_proc)

        if not self.inputMap.kernel_radius == old_kernel_radius:
            # Update gui with new value
            self.doubleSpinBox_kernelRadius.setValue(self.inputMap.kernel_radius)
        else:
            # Propagate to other settings since it won't be triggered by the connect
            self.set_kernel_size()

        # Propagate to other settings
        # self.set_kernel_tau()

    def set_kernel_size(self):
        self.inputMap.kernel_radius = self.doubleSpinBox_kernelRadius.value()
        old_kernel_size = self.inputMap.kernel_size

        # How many pixels do we fit into the significant highest frequency?
        kernel_size = int(np.floor(self.doubleSpinBox_inputLowpass.value() / self.inputMap.voxel_size_proc))
        # Make it an odd size
        kernel_size = ((kernel_size // 2) * 2) + 1
        # It should be larger than 1, and never needs to be bigger than 9.
        kernel_size = np.clip(kernel_size, 3, 9)

        # It makes no sense to make a kernel size larger than that which fits the entire sphere
        upper_limit = np.ceil(self.inputMap.kernel_radius*np.sqrt(3))
        upper_limit = ((upper_limit // 2) * 2) + 1

        self.inputMap.kernel_size = np.min([kernel_size, upper_limit])

        if not self.inputMap.kernel_size == old_kernel_size:
            # Update gui with new value
            self.spinBox_kernelSize.setValue(int(self.inputMap.kernel_size))
        else:
            # Propagate to other settings since it won't be triggered by the connect
            self.set_kernel_tau()



    def set_kernel_tau(self):

        scale_kernel, tau_ana = occupancy.spherical_kernel(
            self.spinBox_kernelSize.value(),
            radius=self.doubleSpinBox_kernelRadius.value()
        )
        self.inputMap.kernel_nv = int(np.sum(scale_kernel))
        self.inputMap.kernel_tau = tau_ana #occupancy.set_tau(n_v=self.inputMap.kernel_nv)

        # Set gui
        emphasis = QtGui.QFont()
        emphasis.setBold(False)
        if self.inputMap.kernel_nv == self.spinBox_kernelSize.value()**3:
            emphasis.setBold(True)
        self.label_samplesValue.setFont(emphasis)
        self.label_samplesValue.setText(str(self.inputMap.kernel_nv))
        self.doubleSpinBox_Tau.setValue(self.inputMap.kernel_tau*100)


    def view_x(self):
        self.checkBox_viewX.setChecked(True)
        self.checkBox_viewY.setChecked(False)
        self.checkBox_viewZ.setChecked(False)
        self.render_all_slices()

    def view_y(self):
        self.checkBox_viewX.setChecked(False)
        self.checkBox_viewY.setChecked(True)
        self.checkBox_viewZ.setChecked(False)
        self.render_all_slices()

    def view_z(self):
        self.checkBox_viewX.setChecked(False)
        self.checkBox_viewY.setChecked(False)
        self.checkBox_viewZ.setChecked(True)
        self.render_all_slices()

    def do_modify(self):
        mod_tab = self.tabWidget_modification.currentIndex()
        if mod_tab == self.tabWidget_modification.indexOf(self.tab_amplification):
            if self.groupBox_amplification.isChecked():
                return(1)
            else:
                pass
        elif mod_tab == self.tabWidget_modification.indexOf(self.tab_attenuation):
            if self.groupBox_attenuation.isChecked():
                return(2)
            else:
                pass

        elif mod_tab == self.tabWidget_modification.indexOf(self.tab_sigmoid):
            if self.groupBox_sigmoid.isChecked():
                return(3)
            else:
                pass

        if self.groupBox_amplification.isChecked():
                return(1)
        if self.groupBox_attenuation.isChecked():
                return(2)
        if self.groupBox_sigmoid.isChecked():
                return(3)

        return(None)

    def render_output_slice_with_focus(self):
        self.update_mod_sliders()
        # Get the mode of modification
        mode = self.do_modify()

        if mode is not None:
            # If either the input or scale map is missing...
            have_input = self.comboBox_inputScale.currentText()
            have_scale = self.comboBox_inputMap.currentText() and self.occ_scale
            have_both = have_input and have_scale

            if not have_both:
                # ...then focus on the plot tab
                self.tabWidget_view.setCurrentIndex(self.tabWidget_view.indexOf(self.tab_viewModification))

            # otherwise check if we are on the mod tab, in which case keep it
            elif self.tabWidget_view.currentIndex() != self.tabWidget_view.indexOf(self.tab_viewModification):
                # ...and which if we are on anything else
                self.tabWidget_view.setCurrentIndex(self.tabWidget_view.indexOf(self.tab_viewOutput))

        self.render_output_slice()

    def render_output_slice(self,force=False):

        self.update_plot_params()

        do_render=False
        output_tab = self.tabWidget_view.currentIndex() == self.tabWidget_view.indexOf(self.tab_viewOutput)

        if output_tab and self.occ_scale:
            do_render = True
        if self.res_scale:
            self.label_viewOutput.clear()
            self.label_viewOutput.setText("The chose scale is not an 'occupancy' \n"
                                          "scale, but a resolution scale. This \n"
                                          "is not appropriate for modification.")
            force = False
            self.update_can_modify()


        if do_render or force:

            input_fileName = self.comboBox_inputMap.currentText()
            scale_fileName = self.comboBox_inputScale.currentText()

            if input_fileName and scale_fileName:
                self.label_viewOutput.setEnabled(True)

                input_f = mf.mmap(input_fileName)
                input_n = input_f.header['nx']

                scale_f = mf.mmap(scale_fileName)
                scale_n = scale_f.header['nx']

                input_slice = self.horizontalSlider_viewSlice.value()
                scale_slice = int((input_slice / float(input_n)) * scale_n)

                tmin = input_f.header['dmin']
                tmax = input_f.header['dmax']

                if self.checkBox_viewX.isChecked():
                    input_t = input_f.data[input_slice-1,:,:]
                    scale_t = scale_f.data[scale_slice-1,:,:]
                elif self.checkBox_viewY.isChecked():
                    input_t = input_f.data[:,input_slice-1,:]
                    scale_t = scale_f.data[:,scale_slice-1,:]
                elif self.checkBox_viewZ.isChecked():
                    input_t = input_f.data[:, :,input_slice-1]
                    scale_t = scale_f.data[:, :,scale_slice-1]

                #print(input_t.shape, scale_t.shape)
                if not input_t.shape == scale_t.shape:
                    input_t = ndi.zoom(input_t,float(scale_n)/float(input_n),order=1)
                N = 100
                mode = self.do_modify()

                x = np.linspace(0,1,N)
                s = []
                if mode == 1: #Amplify
                    s = x ** (1/self.MplWidget_viewModification.amplification_power)
                elif mode == 2: #Attenuate
                    s = x ** (self.MplWidget_viewModification.attenuation_power)
                elif mode == 3: #Sigmoid
                    x,s = occupancy.scale_mapping_sigmoid(self.MplWidget_viewModification.sigmoid_pivot,self.MplWidget_viewModification.sigmoid_power,n=N)

                operations=['amplifying', 'attenuating', 'sigmoiding']
                self.update_can_modify()
                if mode is not None:

                    #print(f'{operations[mode-1]}')
                    #s = np.divide(s,x,where=x!=0)
                    mapped = s[(scale_t*N).astype(int)-1]
                    mod_slice = np.copy(input_t)
                    d_scale_t = (scale_t<0.01).astype(float)
                    d_scale_t += scale_t
                    mod_slice = np.divide(mapped,np.clip(d_scale_t,0,1))

                    #mod_slice = np.divide(mod_slice,scale_t,where=scale_t>=0.05)
                    output_t = np.multiply(input_t,mod_slice)
                    threshold = np.min([0.05,self.MplWidget_viewModification.sigmoid_pivot])

                    output_t =  np.multiply(output_t,scale_t>threshold)
                    output_t += np.multiply(input_t,scale_t<threshold)
                    output_t =  np.clip(output_t,tmin,tmax)
                    output_t =  (output_t-tmin)/(tmax-tmin)

                    im_data = np.array((output_t*255).astype(np.uint8))
                    qimage = QtGui.QImage(im_data,scale_n,scale_n,QtGui.QImage.Format_Grayscale8)
                    pixmap = QtGui.QPixmap(qimage) # Setup pixmap with the provided image
                    pixmap = pixmap.scaled(self.label_viewOutput.width(), self.label_viewOutput.height(), QtCore.Qt.KeepAspectRatio) # Scale pixmap

                    self.label_viewOutput.setPixmap(pixmap) # Set the pixmap onto the label
                    self.label_viewOutput.setAlignment(QtCore.Qt.AlignCenter) # Align the label to center


                    self.label_warnPreview.raise_()
                else:
                    self.label_viewOutput.setText("You have not set to modify anything. \n\n"
                                                  "Enable \"Amplify\", \"Attenuate\", or \n"
                                                  "\"Sigmoid\" on the left and set \n "
                                                  "the power >1.")
        else:
            self.label_viewOutput.setEnabled(False)

    def update_can_modify(self):

        do_attn = self.MplWidget_viewModification.attenuation_power > 1 and self.groupBox_attenuation.isChecked()
        do_sigm = self.MplWidget_viewModification.sigmoid_power > 1 and self.groupBox_sigmoid.isChecked()
        do_ampl = self.MplWidget_viewModification.amplification_power > 1 and self.groupBox_amplification.isChecked()

        can_modify  = False
        if self.comboBox_inputMap.currentText() is not None and self.occ_scale is not None:
            can_modify = self.occ_scale and len(self.comboBox_inputMap.currentText())>3

        if do_attn or do_sigm:
            self.actionmakeSubtractionMask.setEnabled(can_modify)
        else:
            self.actionmakeSubtractionMask.setEnabled(False)

        if do_attn or do_sigm or do_ampl:
            self.toolButton_modify.setEnabled(can_modify)
            self.actionmodifyMap.setEnabled(can_modify)
        else:
            self.toolButton_modify.setEnabled(False)
            self.actionmodifyMap.setEnabled(False)


    def update_plot_params(self):
        self.MplWidget_viewModification.sigmoid_power = self.doubleSpinBox_sigmoidPower.value()
        self.MplWidget_viewModification.sigmoid_pivot = self.doubleSpinBox_sigmoidPivot.value()
        self.MplWidget_viewModification.attenuation_power = self.doubleSpinBox_attnPower.value()
        self.MplWidget_viewModification.amplification_power = self.doubleSpinBox_amplPower.value()
        self.MplWidget_viewModification.amplify = self.groupBox_amplification.isChecked()
        self.MplWidget_viewModification.attenuate = self.groupBox_attenuation.isChecked()
        self.MplWidget_viewModification.sigmoid = self.groupBox_sigmoid.isChecked()

        self.MplWidget_viewModification.plot_modification()
        self.update_can_modify()


    def update_mod_spin_boxes(self):
        self.doubleSpinBox_amplPower.setValue(self.horizontalSlider_amplPower.value()/10.)
        self.doubleSpinBox_attnPower.setValue(self.horizontalSlider_attnPower.value()/10.)
        self.doubleSpinBox_sigmoidPower.setValue(self.horizontalSlider_sigmoidPower.value()/10.)
        self.doubleSpinBox_sigmoidPivot.setValue(self.horizontalSlider_sigmoidPivot.value()/100.0)

    def update_mod_sliders(self):
        self.horizontalSlider_amplPower.setValue(int(self.doubleSpinBox_amplPower.value()*10))
        self.horizontalSlider_attnPower.setValue(int(self.doubleSpinBox_attnPower.value()*10))
        self.horizontalSlider_sigmoidPower.setValue(int(self.doubleSpinBox_sigmoidPower.value()*10))
        self.horizontalSlider_sigmoidPivot.setValue(int(self.doubleSpinBox_sigmoidPivot.value()*100))

    def toggle_scale_mode(self):
        modifying = False
        if self.groupBox_amplification.isChecked():
            modifying = True
        if self.groupBox_attenuation.isChecked():
            modifying = True
        if self.groupBox_sigmoid.isChecked():
            modifying = True

        if not modifying:
            # Don't un-toggle if set
            self.checkBox_scaleOcc.setEnabled(True)
            if self.checkBox_scaleOcc:
                return

        if modifying:
            self.checkBox_scaleOcc.setChecked(True)
            self.checkBox_scaleRes.setChecked(False)
            self.checkBox_scaleOcc.setEnabled(False)
            self.checkBox_scaleRes.setEnabled(False)
        else:
            self.checkBox_scaleOcc.setChecked(False)
            self.checkBox_scaleRes.setChecked(True)
            self.checkBox_scaleOcc.setEnabled(True)
            self.checkBox_scaleRes.setEnabled(True)

    def cat_log(self):
        from pathlib import Path
        run_log = f'log_{str(Path(self.comboBox_inputMap.currentText()).stem)}.txt'
        with open(self.log_file_name, 'a') as outfile:
            with open(run_log) as infile:
                outfile.write('-- START Contents of run log-file: --\n')
                outfile.write(infile.read())
                outfile.write('-- END Contents of run log-file: --\n')

    def occupy_log(self, message, save=True, timestamp=False):
        dt_string = ''
        if timestamp or self.new_session:
            from datetime import datetime
            now = datetime.now()
            dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
            dt_string = f'{self.color_time(dt_string)}\n'

        if message.startswith('** warn **'):
            message = self.color_warn(message)

        if message.startswith('AT:'):
            message = self.color_testing(message)

        message = f'{dt_string} {message}'
        self.textEdit_log.append(message)
        self.textEdit_log.repaint()
        self.jump_to_end_of_log()

        with open(self.log_file_name, "a") as file_open:
            if self.new_session:
                is_fetching_emdb = not (id is None or id == 0)
                if self.comboBox_inputMap.currentText() or is_fetching_emdb:

                    # Which session is this
                    file_r = open(self.log_file_name, "r")
                    data = file_r.read()
                    # get number of occurrences of the substring in the string
                    self.session_no = data.count('NEW GUI SESSION STARTED') + 1
                    # Which session is this

                    # Log that this is a new seesion in the full log
                    file_open.write(f'{dt_string} NEW GUI SESSION STARTED ({self.session_no}) \n\n')
                    self.new_session = False
            if save:
                file_open.write(f'{message}\n')


    def occupy_warn(self, message):
        #warning = "<span style=\" font-size:8pt; font-weight:600; color:#ff0000;\" >"
        warning = self.color_warn(message)
        self.textEdit_log.append(warning)

    def clear_log(self):
        self.textEdit_log.clear()

    def color_time(self,message):
        return self.decorate_color(message,'1f77b4')
    def color_warn(self,message):
        return self.decorate_color(message,'d62728')
    def color_testing(self,message):
        return self.decorate_color(message,'5f8e40')
    def color_run(self,message):
        return self.decorate_color(message,'ff7f0e')

    def decorate_color(self,message,color):
        clr_message = f'<span style=\" color:#{color};\" > {message} </span>'
        return clr_message

    def view_full_log(self):

        self.occupy_log("Opening full log", save=False)
        self.MainWindow_fullLog = fullLog_dialog()
        self.MainWindow_fullLog.make_dialog(self.log_file_name)

        with open(self.log_file_name) as gui_log:
            for line in gui_log:
                self.MainWindow_fullLog.logText.append(line.rstrip('\n'))
        self.MainWindow_fullLog.show()

    def is_tool(self,name):
        """Check whether `name` is on PATH and marked as executable."""

        from shutil import which
        return which(name)

    def detect_OS(self):
        self.os = None
        import sys

        os_platform = (sys.platform).lower()

        if "darwin" in os_platform:
            self.os = "Mac"
        elif "win" in os_platform:
            self.os = "Windows"
        elif "linux" in os_platform:
            self.os = "Linux"
        else:
            self.os = "Unknown"

        self.occupy_log(f'AT: Detected OS:{self.os}')

    def find_chimerax(self,name):
        self.occupy_log(f'AT: current chimx:{self.chimerax_name}')
        if self.chimerax_name is None:
            self.occupy_log(f'AT: looking for {name}')
            self.chimerax_name = self.is_tool(name)

            if self.chimerax_name is not None:
                self.occupy_log(f'AT: found chimX:{self.chimerax_name}')
                if self.os == "Windows":
                    # Windows has system directories with spaces but is fussy about calling them. How consistent.
                    self.chimerax_name = self.chimerax_name.replace(" ", "\" \"")
                    self.occupy_log(f'AT: on win, setting chimX:{self.chimerax_name}')
        else:
            self.occupy_log(f'AT:  skipping {name}')


    def have_chimerax(self):
        import os

        self.chimerax_name = None

        self.find_chimerax("chimerax")
        self.find_chimerax("xchimera")
        self.find_chimerax("Chimerax")
        self.find_chimerax("ChimeraX")

        if self.os == "Windows":
            self.find_chimerax('C:\Program\" \"Files\ChimeraX\bin\ChimeraX.exe')

        occupy_chimx_var = 'OCCUPY_CHIMERAX'
        if os.environ.get(occupy_chimx_var) != None:
            self.find_chimerax(os.environ.get(occupy_chimx_var))

    def run_chimerax(self):
        if self.chimerax_file_name is not None:
            self.jump_to_end_of_log()

            self.occupy_log(f'AT: Detected chimerax: {self.chimerax_name}')

            import os

            cmd_to_run = ' '
            if self.os == "Windows":
                cmd_to_run = f'{self.chimerax_name} {self.chimerax_file_name}'
            else:
                cmd_to_run = f'{self.chimerax_name} {self.chimerax_file_name} &'

            self.occupy_log(f'AT: Starting chimeraX: {cmd_to_run}')

            with Capturing() as output:
                os.system(cmd_to_run)

            for i in output:
                self.occupy_log(f'AT:  chimX: {i}')

        else:
            self.occupy_log("No chimerax file defined this session.")


    def generate_soldef_from_scale(self):

        threshold = float(self.slider_scaleAsSolDef.value()) / 100.0
        solvent_def_name = f'soldef_by_scale_{threshold}.mrc'

        from os.path import exists

        if not exists(solvent_def_name):
            scale_file_name = self.comboBox_inputScale.currentText()
            f_in = mf.mmap(scale_file_name, 'r')

            data = np.copy(f_in.data)

            parent = self.comboBox_inputScale.currentText()
            out_size = np.shape(data)[0]

            if self.infile_size is not None:
                parent = self.comboBox_inputMap.currentText()
                out_size = self.infile_size
            if f_in.header['nx'] != self.infile_size:
                data, _ = map_tools.lowpass(
                    data,
                    output_size=out_size
                )

            data = (data > threshold).astype(np.float32)
            map_tools.new_mrc(
                data=data,
                file_name=solvent_def_name,
                parent=parent
            )

            f_in.close()

        self.set_solvent_file(solvent_def_name)
        self.checkBox_scaleAsSolDef.setChecked(False)
        self.slider_scaleAsSolDef.setEnabled(False)
        return solvent_def_name

    def compose_cmd(self,only_estimate=None):

        options = args.occupy_options()
        self.cmd.clear()
        self.cmd.append('occupy')

        # input files ----------------------------------------------------------------------------
        options.input_map = self.comboBox_inputMap.currentText()
        self.cmd.append(f'--input-map {options.input_map}')

        if self.checkBox_scaleAsSolDef.isChecked():
            options.solvent_def = self.generate_soldef_from_scale()

        if len(self.comboBox_inputSolventDef.currentText())>3:
            options.solvent_def = self.comboBox_inputSolventDef.currentText()
            self.cmd.append(f'--solvent-def {options.solvent_def}')

        # input options-------------------------------------------------------------------------
        options.lowpass_input = self.doubleSpinBox_inputLowpass.value()
        self.cmd.append(f'--lowpass {options.lowpass_input}')
        options.kernel_size = self.spinBox_kernelSize.value()
        self.cmd.append(f'--kernel-size {options.kernel_size}')
        options.kernel_radius = self.doubleSpinBox_kernelRadius.value()
        self.cmd.append(f'--kernel-radius {options.kernel_radius}')
        options.tau = self.doubleSpinBox_Tau.value()/100.0
        self.cmd.append(f'--tau  {options.tau:.4f}')
        options.tile_size = self.spinBox_tileSize.value()
        self.cmd.append(f'--tile-size {options.tile_size}')


        # max-box -----------------------------------------------------------------------------
        if self.checkBox_maxBox.isChecked():
            options.max_box = self.spinBox_maxBox.value()
            self.cmd.append(f'--max-box {options.max_box}')
        else:
            options.max_box = self.spinBox_maxBox.value()
            self.cmd.append(f'--max-box -1')

        modifying = False
        # modification options ---------------------------------------------------------------
        if not only_estimate:
            modifying = False
            if self.groupBox_amplification.isChecked():
                modifying = True
                options.amplify = self.doubleSpinBox_amplPower.value()
                self.cmd.append(f'--amplify {options.amplify}')

            if self.groupBox_attenuation.isChecked():
                modifying = True
                options.attenuate = self.doubleSpinBox_attnPower.value()
                self.cmd.append(f'--attenuate {options.attenuate}')

            if self.groupBox_sigmoid.isChecked():
                modifying = True
                options.sigmoid = self.doubleSpinBox_sigmoidPower.value()
                options.pivot = self.doubleSpinBox_sigmoidPivot.value()
                self.cmd.append(f'--sigmoid {options.sigmoid } --pivot {options.pivot}')


        # output options -------------------------------------------------------------------
        if self.checkBox_outputLowpass.isChecked():
            options.lowpass_output = self.doubleSpinBox_outputLowpass.value()
            self.cmd.append(f'--output-lowpass {options.lowpass_output}')

        if self.checkBox_suppresSolvent.isChecked():
            options.exclude_solvent = True
            self.cmd.append(f'--suppress-solvent')

        if self.checkBox_S0.isChecked():
            options.s0 = True
            self.cmd.append(f'-S0')

        if self.checkBox_histMatch.isChecked():
            options.hist_match = True
            self.cmd.append(f'--hist-match')

        if self.checkBox_scaleOcc.isChecked():
            options.scale_mode = 'occ'
            if not modifying:
                # By default we include resolution-dependent effects when not modifying,
                # so we need to tell occupy to omit them
                options.lp_scale = True
                self.cmd.append(f'--occupancy')
        else:
            options.scale_mode = 'res'
            if modifying:
                options.lp_scale = False
                self.occupy_warn('Modifying with resolution-effect is not recommended. I suggest ticking "occupancy" instead.')

        if self.action_verbose.isChecked():
            options.verbose = True
            self.cmd.append(f'--verbose')

        # Always plot in GUI
        options.plot = True
        self.cmd.append(f'--plot')

        options.gui = True

        return options

    def log_new_run(self,start=True):
        phase = ''
        if start:
            self.run_no += 1
            phase = 'STARTING'
        else:
            phase = 'FINISHED'

        self.occupy_log(self.color_run(f'{phase} run no {self.session_no}-{self.run_no}'), timestamp=True)

    def print_command(self):

        if len(self.comboBox_inputMap.currentText())>3:
            options = self.compose_cmd()

            self.occupy_log(" Reporting command: \n")
            self.occupy_log(f'{" ".join(self.cmd)}\n')
        else:
            self.occupy_log("provide an input file to print a working command",save=False)

    def estimate_scale(self):
        self.run_cmd(only_estimate=True)

    def jump_to_end_of_log(self):
        self.textEdit_log.verticalScrollBar().setValue(self.textEdit_log.verticalScrollBar().maximum())

    def run_cmd(self, only_estimate=False):

        self.jump_to_end_of_log()

        options = self.compose_cmd(only_estimate=only_estimate)

        self.toolButton_chimerax.setEnabled(False)
        self.toolButton_estimateScale.setEnabled(False)
        self.actionestimateScale.setEnabled(self.toolButton_estimateScale.isEnabled())
        self.log_new_run(start=True)
        with Capturing() as output:
            #self.occupy_log('Estimating local scale...')
            estimate.occupy_run(options)

        for i in output:
            self.occupy_log(i)

        # Report details to gui log file even if not verbose.
        if not options.verbose:
            self.cat_log()

        self.log_new_run(start=False)

        from pathlib import Path
        new_name = Path(options.input_map).name
        # Force .mrc for output
        new_name = f'{Path(new_name).stem}.mrc'
        self.confidence_file_name = f'conf_{Path(new_name).stem}.mrc'

        scale_mode = 'res'
        if self.checkBox_scaleOcc.isChecked():
            scale_mode = 'occ'
        if options.s0:
            scale_mode = f'naive_{scale_mode}'

        self.add_scale_file(f'scale_{scale_mode}_{Path(new_name).stem}.mrc')

        self.chimerax_file_name = f'chimX_{Path(new_name).stem}.cxc'
        if self.chimerax_name is not None:
            self.toolButton_chimerax.setEnabled(True)
            self.toolButton_chimerax.setToolTip(f'Run the chimerax command script \n to visualize the most recent  \n output from occupy. \n\n ({self.chimerax_file_name})')
        self.toolButton_estimateScale.setEnabled(True)
        self.actionestimateScale.setEnabled(self.toolButton_estimateScale.isEnabled())

        self.show_solvent_model()

    def show_solvent_model(self):
        from pathlib import Path
        solDef_specifier = ''
        c = self.comboBox_inputSolventDef.currentText()
        if self.comboBox_inputSolventDef.currentText() != ' ':
            solDef_specifier = f'{Path(self.comboBox_inputSolventDef.currentText()).stem}_'
        solModel_file_name = f'solModel_{solDef_specifier}' + Path(self.comboBox_inputMap.currentText()).stem + '.png'

        self.solModel_file_name = solModel_file_name
        pixmap = QtGui.QPixmap(self.solModel_file_name)  # Setup pixmap with the provided image
        pixmap = pixmap.scaled(self.label_solventModel.width(), self.label_solventModel.height(),
                               QtCore.Qt.KeepAspectRatio)  # Scale pixmap
        self.label_solventModel.setPixmap(pixmap)  # Set the pixmap onto the label
        self.label_solventModel.setAlignment(QtCore.Qt.AlignCenter)  # Align the label to center

        self.toolButton_expandSolModel.setEnabled(True)

    def window_solvent_model(self):

        self.MainWindow_solModel = ImageWindow()

        screen = QtWidgets.QApplication.primaryScreen()
        size = screen.size()
        rect = screen.availableGeometry()

        self.occupy_log(f'AT: Screen: {screen.name()}')
        self.occupy_log(f'AT: Screen w/h: {size.width()}/{size.height()}')
        self.occupy_log(f'AT: Avail w/h: {rect.width()}/{rect.height()}')

        # The image will be 1200:252 pixels.
        # Assume width-limited and make as big as possible.
        rect_width = rect.width()
        rect_height = int(rect_width * 252 / 1200)
        window = QtWidgets.QLabel(self.MainWindow_solModel)
        pixmap = QtGui.QPixmap(self.solModel_file_name)
        pixmap = pixmap.scaled(
            rect_width-20,
            rect_height-20,
            QtCore.Qt.KeepAspectRatio,
            QtCore.Qt.SmoothTransformation
        )  # Scale pixmap
        self.MainWindow_solModel.resize(rect_width,rect_height)
        self.MainWindow_solModel.setFixedSize(rect_width,rect_height)
        window.setGeometry(QtCore.QRect(10, 10, rect_width-20, rect_height-20))
        window.setPixmap(pixmap)
        self.MainWindow_solModel.setWindowTitle(f'{os.getcwd()}/{self.solModel_file_name}')
        self.MainWindow_solModel.show()

    def window_about(self):

        self.MainWindow_about = ImageWindow()
        self.MainWindow_about.resize(580, 160)
        self.MainWindow_about.setWindowTitle("About OccuPy")

        self.centralwidget_about = QtWidgets.QWidget(self.MainWindow_about)
        self.centralwidget_about.setObjectName("centralwidget")
        self.horizontalLayoutWidget_about = QtWidgets.QWidget(self.centralwidget_about)
        self.horizontalLayoutWidget_about.setGeometry(QtCore.QRect(10, 10, 550, 140))
        self.horizontalLayoutWidget_about.setObjectName("horizontalLayoutWidget")
        self.horizontalLayout_about = QtWidgets.QHBoxLayout(self.horizontalLayoutWidget_about)

        self.horizontalLayout_about.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_about.setObjectName("horizontalLayout")
        self.window_about = QtWidgets.QLabel(self.horizontalLayoutWidget_about)
        self.window_about.setObjectName("label")

        self.horizontalLayout_about.addWidget(self.window_about)
        self.verticalLayout_about = QtWidgets.QVBoxLayout()
        self.verticalLayout_about.setObjectName("verticalLayout")

        self.label_title_and_version = QtWidgets.QLabel(self.horizontalLayoutWidget_about)
        self.label_title_and_version.setObjectName("label_title_and_version")
        self.verticalLayout_about.addWidget(self.label_title_and_version)

        self.label_cite = QtWidgets.QLabel(self.horizontalLayoutWidget_about)
        self.label_cite.setObjectName("label_cite")
        self.verticalLayout_about.addWidget(self.label_cite)

        self.label_developers = QtWidgets.QLabel(self.horizontalLayoutWidget)
        self.label_developers.setObjectName("label_developers")
        self.verticalLayout_about.addWidget(self.label_developers)

        self.label_issues = QtWidgets.QLabel(self.horizontalLayoutWidget)
        self.label_issues.setObjectName("label_issues")
        self.verticalLayout_about.addWidget(self.label_issues)

        self.label_contact = QtWidgets.QLabel(self.horizontalLayoutWidget)
        self.label_contact.setObjectName("label_contact")
        self.verticalLayout_about.addWidget(self.label_contact)

        self.horizontalLayout_about.addLayout(self.verticalLayout_about)
        self.MainWindow_about.setCentralWidget(self.centralwidget_about)


        from pkg_resources import get_distribution
        __version__ = get_distribution("occupy").version
        # Make the labels
        self.label_title_and_version.setText(f'OccuPy {__version__}')
        self.label_title_and_version.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)

        url_pub = "<a href=\"https://occupy.readthedocs.io/en/latest/about/\">the paper</a>"
        self.label_cite.setText(f'Please cite {url_pub}')
        self.label_cite.setOpenExternalLinks(True)

        self.label_developers.setText("Developed by Bjoern Forsberg, Pranav Shah and Alister Burt")

        url_issues = "<a href=\"https://github.com/bforsbe/OccuPy/issues\">issues</a>"
        self.label_issues.setText(f'Report (and view known) {url_issues}')
        self.label_issues.setOpenExternalLinks(True)

        url_email = "<a href=\"mailto:bjorn.forsberg@ki.se\">bjorn.forsberg@ki.se</a>"
        self.label_contact.setText(f'Contact {url_email}')
        self.label_contact.setOpenExternalLinks(True)

        # Set the image
        pixmap = QtGui.QPixmap(self.icon_large)
        pixmap = pixmap.scaled(
            140,
            140,
            QtCore.Qt.KeepAspectRatio
        )  # Scale pixmap
        self.window_about.setPixmap(pixmap)

        self.MainWindow_about.show()

    def change_current_dir(self):
        new_directory = QtWidgets.QFileDialog.getExistingDirectory(None, "Select Directory", "")  # Ask for dir
        import os

        if new_directory != '':
            if os.path.isdir(new_directory):
                os.chdir(new_directory)
                self.occupy_log(f' Changed directory to {new_directory}')
                self.reset_session()
            else:
                self.occupy_warn(f' Cannot change directory to {new_directory}')
        else:
            self.occupy_log(f'AT: staying in {os.getcwd()}')

class MyWindow(QtWidgets.QMainWindow):
    def closeEvent(self,event):
        result = QtWidgets.QMessageBox.question(self,
                      "Confirm exit",
                      "\nClose OccuPy GUI?",
                      QtWidgets.QMessageBox.Yes| QtWidgets.QMessageBox.Cancel)
        event.ignore()

        if result == QtWidgets.QMessageBox.Yes:
            event.accept()

class ImageWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(ImageWindow, self).__init__(parent)


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = MyWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())


