import sys
from PCANBasic import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import threading
import struct
import time
import numpy as np
import glob
import os
from plot_graph import *

# Import separated modules
from ui_widgets import TitleLabel, TextLabel, LabeledLineEdit, TimerRepeater
from constants import *
from message_handler import pack_sdo_unit, flatten_list, float_to_byte_list, get_dlc_from_length
from pcan_communicator import PCANCommunicator
from robot_controller import RobotController
from sysid_controller import SystemIDController
from data_manager import DataManager
from parameter_controller import ParameterController
from ui_builder import UIBuilder
class GUI(QWidget):
    ## Node ID
    node_id = 0x07  # LEFT

    trigger_stop_sysid = pyqtSignal()
    
    def __init__(self, PcanHandle=PCAN_USBBUS1, IsFD=True, Bitrate=PCAN_BAUD_1M, 
                 BitrateFD=b'f_clock_mhz=80,nom_brp=10,nom_tseg1=5,nom_tseg2=2,nom_sjw=2,data_brp=1,data_tseg1=11,data_tseg2=4,data_sjw=4'):
        super().__init__()
        """
        Initialize and start the program
        """
        # Initialize PCAN communicator
        self.pcan_comm = PCANCommunicator(PcanHandle, IsFD, Bitrate, BitrateFD)
        
        # Initialize controllers
        self.robot_ctrl = RobotController(self.pcan_comm, self.node_id)
        self.sysid_ctrl = SystemIDController(self.pcan_comm, self.node_id)
        self.data_mgr = DataManager(self.pcan_comm)
        self.param_ctrl = ParameterController(self.pcan_comm, self.node_id)
        
        # UI Builder
        self.ui_builder = UIBuilder()
        
        self.TimerInterval = 1000
        self.sysid_done = 0
        self.m_thread_run = False
        self.m_obj_thread = None
        
        # Initialize UI
        self.initUI()
        self.connect_pcan()
        self.trigger_stop_sysid.connect(self.sysid_stop)


    def initUI(self):
        # Create all UI components
        self.ui_builder.create_buttons()
        self.ui_builder.create_labels()
        self.ui_builder.create_checkboxes()
        self.ui_builder.create_title_labels()
        
        # Store references to UI components
        self.buttons = self.ui_builder.buttons
        self.labels = self.ui_builder.labels
        self.checkboxes = self.ui_builder.checkboxes
        self.other_widgets = self.ui_builder.other_widgets
        self.tabs_ref = self.ui_builder.tabs.get('ref')
        self.tab_walking = self.ui_builder.tabs.get('walking')
        self.tab_sine = self.ui_builder.tabs.get('sine')
        self.tab_square = self.ui_builder.tabs.get('square')
        self.tab_ankle = self.ui_builder.tabs.get('ankle')
        
        # For backward compatibility with existing code
        self.infoBox = self.other_widgets['infoBox']
        self.sysid_infoBox = self.other_widgets['sysid_infoBox']
        self.file_name = self.other_widgets['file_name']
        
        # Access buttons by old names
        self.button_inittorque = self.buttons['inittorque']
        self.button_roboton = self.buttons['roboton']
        self.button_assiston = self.buttons['assiston']
        self.button_robotoff = self.buttons['robotoff']
        self.button_assistoff = self.buttons['assistoff']
        self.button_capture = self.buttons['capture']
        self.button_stop = self.buttons['stop']
        self.button_plot = self.buttons['plot']
        self.button_save = self.buttons['save']
        self.button_setCtrl = self.buttons['setCtrl']
        self.button_setParam = self.buttons['setParam']
        self.button_shiftright = self.buttons['shiftright']
        self.button_shiftleft = self.buttons['shiftleft']
        self.button_connect = self.buttons['connect']
        self.button_sysid_start = self.buttons['sysid_start']
        self.button_sysid_stop = self.buttons['sysid_stop']
        self.button_sysid_apply = self.buttons['sysid_apply']
        self.button_sysid_save = self.buttons['sysid_save']
        
        # Connect signals
        self.button_inittorque.clicked.connect(self.init_torque)
        self.button_roboton.clicked.connect(self.robot_on)
        self.button_robotoff.clicked.connect(self.robot_off)
        self.button_assiston.clicked.connect(self.assist_on)
        self.button_assistoff.clicked.connect(self.assist_off)
        self.button_capture.clicked.connect(self.capture_data)
        self.button_stop.clicked.connect(self.stop_capture)
        self.button_plot.clicked.connect(self.plot_graph)
        self.button_save.clicked.connect(self.save_data_to_txt)
        self.button_setCtrl.clicked.connect(self.set_ctrl)
        self.button_setParam.clicked.connect(self.set_param)
        self.button_shiftleft.clicked.connect(self.shift_left)
        self.button_shiftright.clicked.connect(self.shift_right)
        self.button_connect.clicked.connect(self.test)
        self.button_sysid_apply.clicked.connect(self.sysid_apply)
        self.button_sysid_start.clicked.connect(self.sysid_start)
        self.button_sysid_stop.clicked.connect(self.sysid_stop)
        self.button_sysid_save.clicked.connect(self.sysid_save_data_to_txt)
        
        # Set checkable
        self.button_roboton.setCheckable(True)
        self.button_robotoff.setCheckable(True)
        self.button_assiston.setCheckable(True)
        self.button_assistoff.setCheckable(True)
        self.button_capture.setCheckable(True)
        self.button_stop.setCheckable(True)
        
        # Build main window
        self.ui_builder.build_main_window(self)
        self.routine_list=[self.ROUTINE_ID_MIDLEVEL_ANKLE_REF,self.ROUTINE_ID_MIDLEVEL_DISTURBANCE_OBS, 
                           self.ROUTINE_ID_MIDLEVEL_FEEDFORWARD_FILTER, self.ROUTINE_ID_MIDLEVEL_LINEARIZE_STIFFNESS, self.ROUTINE_ID_MIDLEVEL_POSITION_CTRL]
        self.output_filename=''
        ##################################################################
        ######################### BUTTONS ################################
        ##################################################################
        self.button_inittorque = QPushButton('Initiate Torque')
        self.button_inittorque.setStyleSheet("background-color: black; color: white; font-size: 12pt; font-weight: bold;")
        self.button_inittorque.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.button_roboton = QPushButton('Robot On')
        self.button_roboton.setStyleSheet("background-color: blue; color: white; font-size: 12pt; font-weight: bold;")
        self.button_roboton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.button_assiston = QPushButton('Assist On')
        self.button_assiston.setStyleSheet("background-color: blue; color: white; font-size: 12pt; font-weight: bold;")
        self.button_assiston.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.button_robotoff = QPushButton('Robot Off')
        self.button_robotoff.setStyleSheet("background-color: red; color: white; font-size: 12pt; font-weight: bold;")
        self.button_robotoff.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.button_assistoff = QPushButton('Assist Off')
        self.button_assistoff.setStyleSheet("background-color: red; color: white; font-size: 12pt; font-weight: bold;")
        self.button_assistoff.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.button_capture = QPushButton("CAPTURE")
        self.button_capture.setStyleSheet("background-color: black; color: white;font-size: 12pt; font-weight: bold;")
        self.button_capture.setFixedSize(150,50)
        self.button_stop = QPushButton("STOP")
        self.button_stop.setStyleSheet("background-color: red; color: white;font-size: 12pt; font-weight: bold;")
        self.button_stop.setFixedSize(150,50)
        self.button_plot = QPushButton("PLOT")
        self.button_plot.setStyleSheet("background-color: blue; color: white;font-size: 12pt; font-weight: bold;")
        self.button_plot.setFixedSize(150,50)
        self.button_save = QPushButton("SAVE")
        self.button_save.setStyleSheet("background-color: blue; color: white;font-size: 12pt; font-weight: bold;")
        self.button_save.setFixedSize(150,50)

        self.button_setCtrl = QPushButton("SET")
        self.button_setCtrl.setStyleSheet("background-color: black; color: white;font-size: 12pt; font-weight: bold;")
        self.button_setCtrl.setFixedSize(150,50)
        self.button_setParam = QPushButton("SET PARAMETER")
        self.button_setParam.setStyleSheet("background-color: black; color: white;font-size: 12pt; font-weight: bold;")
        self.button_setParam.setFixedSize(200,50)
        self.button_shiftright = QPushButton("->")
        self.button_shiftright.setStyleSheet("background-color: black; color: white;font-size: 12pt; font-weight: bold;")
        self.button_shiftright.setFixedSize(100,50)
        self.button_shiftleft = QPushButton("<-")
        self.button_shiftleft.setStyleSheet("background-color: black; color: white;font-size: 12pt; font-weight: bold;")
        self.button_shiftleft.setFixedSize(100,50)
        self.button_connect = QPushButton("TEST")
        self.button_connect.setStyleSheet("background-color: black; color: white;font-size: 12pt; font-weight: bold;")
        self.button_connect.setFixedSize(150,50)

        self.button_sysid_start = QPushButton("Start ID")
        self.button_sysid_start.setStyleSheet("background-color: black; color: white;font-size: 12pt; font-weight: bold;")
        self.button_sysid_start.setFixedSize(150,50)

        self.button_sysid_stop = QPushButton("Stop ID")
        self.button_sysid_stop.setStyleSheet("background-color: red; color: white;font-size: 12pt; font-weight: bold;")
        self.button_sysid_stop.setFixedSize(150,50)
        self.button_sysid_apply = QPushButton("Apply")
        self.button_sysid_apply.setStyleSheet("background-color: black; color: white;font-size: 12pt; font-weight: bold;")
        self.button_sysid_apply.setFixedSize(150,50)
        self.button_sysid_save = QPushButton("SAVE")
        self.button_sysid_save.setStyleSheet("background-color: blue; color: white;font-size: 12pt; font-weight: bold;")
        self.button_sysid_save.setFixedSize(150,50)

        self.button_inittorque.clicked.connect(self.init_torque)
        self.button_roboton.clicked.connect(self.robot_on)
        self.button_robotoff.clicked.connect(self.robot_off)
        self.button_assiston.clicked.connect(self.assist_on)
        self.button_assistoff.clicked.connect(self.assist_off)
        self.button_capture.clicked.connect(self.capture_data)
        self.button_stop.clicked.connect(self.stop_capture)
        self.button_plot.clicked.connect(self.plot_graph)
        self.button_save.clicked.connect(self.save_data_to_txt)
        self.button_setCtrl.clicked.connect(self.set_ctrl)
        self.button_setParam.clicked.connect(self.set_param)
        self.button_shiftleft.clicked.connect(self.shift_left)
        self.button_shiftright.clicked.connect(self.shift_right)
        self.button_connect.clicked.connect(self.test)
        self.button_sysid_apply.clicked.connect(self.sysid_apply)
        self.button_sysid_start.clicked.connect(self.sysid_start)
        self.button_sysid_stop.clicked.connect(self.sysid_stop)
        self.button_sysid_save.clicked.connect(self.sysid_save_data_to_txt)
        self.button_roboton.setCheckable(True)
        self.button_robotoff.setCheckable(True)
        self.button_assiston.setCheckable(True)
        self.button_assistoff.setCheckable(True)
        self.button_capture.setCheckable(True)
        self.button_stop.setCheckable(True)
        # self.button_plot.setCheckable(True)
        # self.button_save.setCheckable(True)
        ##################################################################
        ######################### Titles #################################
        ##################################################################
        self.rx_title=TitleLabel('Data Acquisition')
        self.ctrl_title=TitleLabel('Controller Setting')
        self.param_title=TitleLabel('Parameter Setting')
        self.imp_ctrl_title=TitleLabel('Impedance Setting')
        ##################################################################
        ######################### Label  #################################
        ##################################################################
        self.Cnt_label=lb('Count(ms):')
        self.Ref_label=lb('Ref(Nm):')
        self.Act_label=lb('Act(Nm):')
        self.Phase_label=lb('Phase(%):')
        self.Enc1_label=lb('Enc1(deg):')
        self.Enc2_label=lb('Enc2(deg):')
        self.Input_label=lb('Input(A):')
        self.Dist_label=lb('Dist(A):')
        self.Linear_label=lb('Linear(A):')
        self.Limit_label=lb('Limit(A):',6)
        self.Plantar_label=lb('Plantar Amp(Nm):',5)
        self.Dorsi_label=lb('Dorsi peak(deg):',5)
        self.Dorsi_label2=lb('Dorsi terminal(deg):',0)
        self.T1_label=lb('Peak Time(%):',55)
        self.T2_label=lb('Ratio :',0.714)
        self.T3_label=lb('Width(%):',60)
        self.T4_label=lb('Peak Duration(%)):',0)
        self.T5_label=lb('Dorsi Initial(%):',0)
        self.T6_label=lb('Peak(%):',0)
        self.T7_label=lb('Terminal(%):',0)
        self.Kp_label=lb('Kp:', 0.2)
        self.Kd_label=lb('Kd:', 0.0001)
        self.plantar_init_label=lb('Plantar Init(%):')
        self.plantar_init_label.lineEdit.setReadOnly(True)
        self.plantar_terminal_label=lb('Terminal(%):')
        self.plantar_terminal_label.lineEdit.setReadOnly(True)

        self.imp_kp_label=lb('Kp:', 11.73)
        self.imp_kd_label=lb('Kd:', 0.83)
        self.imp_lambda_label=lb('lambda:', 0)
        self.imp_epsilon_label=lb('epsilon:', 0)

        self.Max_error=lb('Maximum Error(N):', 30)
        self.Max_ank_ang=lb('Max(D)(deg):', 20)
        self.Min_ank_ang=lb('ROM Min(P) (deg):', -35)

        self.reftanh_amp_label=lb('Amplitude (Nm):', 5)
        self.reftanh_a_label=lb('a:', 10)
        self.reftanh_td_label=lb('duration(s):', 1)

        self.refsine_amp_label=lb('Amplitude (Nm):', 5)
        self.refsine_freq_label=lb('Frequency (Hz):', 1)

        self.refAnkle_amp_label=lb('Plantar Amp(Nm):',5)
        self.refAnkle_peak_label=lb('Peak Time(%):',55)
        self.refAnkle_ratio_label=lb('Ratio :',0.6)
        self.refAnkle_width_label=lb('Width(%):',60)
        self.refAnkle_gaitperiod_label=lb('Gait Period (ms):',2000)
        self.phase_shift_label=lb('Phase Shift (%):',0)

        self.PD = QCheckBox('PD')
        self.DOB = QCheckBox('DOB')
        self.FF = QCheckBox('FF')
        self.LS = QCheckBox('vel_ctrl')
        self.Fric = QCheckBox('Ankle_Comp')
        self.PD.setChecked(True)
        self.DOB.setChecked(False)
        self.FF.setChecked(False)
        self.LS.setChecked(True)
        self.Fric.setChecked(False)
        ##### system id
        self.sysid_infoBox=QLineEdit('')
        self.sysid_infoBox.setReadOnly(True)
        self.sysid_freq_min=lb('Minimum Freq (Hz):', 0.2)
        self.sysid_freq_max=lb('Maximum Freq (Hz):', 2)
        self.sysid_n_sample=lb('Number of Freq:', 5)
        self.sysid_n_iter=lb('Number of iteration:', 5)
        self.sysid_mag=lb('Input Magnitude (A)', 0)
        self.sysid_offset=lb('Input Offset', 0)
        self.sysid_file_name=lb('File Save Name (.txt)', "250304_Flexi_Ankle_ID")
        ##################################################################
        ######################### Layout  ################################
        ##################################################################
        self.grid = QGridLayout()
        self.layout_ctrl = QGridLayout()
        self.layout_ctrl.addWidget(self.ctrl_title,0,0,1,2)
        self.layout_ctrl.addWidget(self.PD,1,0)
        self.layout_ctrl.addWidget(self.DOB,1,1)
        self.layout_ctrl.addWidget(self.FF,2,0)
        self.layout_ctrl.addWidget(self.LS,2,1)
        self.layout_ctrl.addWidget(self.Fric,3,0)
        self.layout_ctrl.addWidget(self.Limit_label,4,0,1,2)
        self.layout_ctrl.addWidget(self.Kp_label,5,0)
        self.layout_ctrl.addWidget(self.Kd_label,5,1)
        self.layout_ctrl.addWidget(self.Max_error,6,0)
        self.layout_ctrl.addWidget(self.Min_ank_ang,7,0)
        self.layout_ctrl.addWidget(self.Max_ank_ang,7,1)

        self.layout_ctrl.addWidget(self.imp_ctrl_title,8,0,1,2)
        self.layout_ctrl.addWidget(self.imp_kp_label,9,0)
        self.layout_ctrl.addWidget(self.imp_kd_label,9,1)
        self.layout_ctrl.addWidget(self.imp_lambda_label,10,0)
        self.layout_ctrl.addWidget(self.imp_epsilon_label,10,1)

        self.layout_ctrl.addWidget(self.button_setCtrl,11,0,1,2)

        self.layout_param = QVBoxLayout()
        self.grid_param=QGridLayout()
        self.grid_param.addWidget(self.Plantar_label,0,0,1,2)
        self.grid_param.addWidget(self.T1_label,1,1)
        self.grid_param.addWidget(self.plantar_init_label,1,0)
        self.grid_param.addWidget(self.plantar_terminal_label,1,2)

        self.grid_param.addWidget(self.T2_label,2,0)
        self.grid_param.addWidget(self.T3_label,2,1)
        self.grid_param.addWidget(self.T4_label,2,2)
        self.grid_param.addWidget(self.Dorsi_label,3,0)
        self.grid_param.addWidget(self.Dorsi_label2,3,1)
        self.grid_param.addWidget(self.T5_label,4,0)
        self.grid_param.addWidget(self.T6_label,4,1)
        self.grid_param.addWidget(self.T7_label,4,2)
        self.grid_param.addWidget(self.phase_shift_label,5,0)

        self.layout_tanh = QVBoxLayout()
        self.layout_tanh.addWidget(self.reftanh_amp_label)
        self.layout_tanh.addWidget(self.reftanh_a_label)
        self.layout_tanh.addWidget(self.reftanh_td_label)
        self.layout_sine = QVBoxLayout()
        self.layout_sine.addWidget(self.refsine_amp_label)
        self.layout_sine.addWidget(self.refsine_freq_label)
        self.layout_ankle = QVBoxLayout()
        self.layout_ankle.addWidget(self.refAnkle_amp_label)
        self.layout_ankle.addWidget(self.refAnkle_peak_label)
        self.layout_ankle.addWidget(self.refAnkle_ratio_label)
        self.layout_ankle.addWidget(self.refAnkle_width_label)
        self.layout_ankle.addWidget(self.refAnkle_gaitperiod_label)

        self.tabs_ref = QTabWidget()
        self.tab_walking=QWidget()
        self.tab_sine=QWidget()
        self.tab_square=QWidget()
        self.tab_ankle=QWidget()
        self.tab_walking.setLayout(self.grid_param)
        self.tab_sine.setLayout(self.layout_sine)
        self.tab_square.setLayout(self.layout_tanh)
        self.tab_ankle.setLayout(self.layout_ankle)
        self.tabs_ref.addTab(self.tab_walking,"Walking")
        self.tabs_ref.addTab(self.tab_sine,"Sine")
        self.tabs_ref.addTab(self.tab_square,"Square")
        self.tabs_ref.addTab(self.tab_ankle,"Ankle")

        self.layout_param.addWidget(self.param_title)
        self.layout_param.addStretch(1)
        self.layout_param.addWidget(self.tabs_ref)
        self.layout_param.addStretch(1)
        self.layout_button=QHBoxLayout()
        self.layout_button.addWidget(self.button_setParam)
        self.layout_button.addWidget(self.button_shiftleft)
        self.layout_button.addWidget(self.button_shiftright)
        self.layout_param.addLayout(self.layout_button)

        self.grid.addWidget(self.button_inittorque, 0,0, 1,0)
        self.grid.addWidget(self.button_roboton, 1, 0)  # 첫 번째 행, 첫 번째 열
        self.grid.addWidget(self.button_assiston, 1, 1)  # 첫 번째 행, 두 번째 열
        self.grid.addWidget(self.button_robotoff, 3, 0)  # 두 번째 행, 첫 번째 열
        self.grid.addWidget(self.button_assistoff, 3, 1)  # 두 번째 행, 두 번째 열

        self.RX_grid=QGridLayout()
        self.RX_grid.addWidget(self.Cnt_label,0,0)
        self.RX_grid.addWidget(self.Ref_label,0,1)
        self.RX_grid.addWidget(self.Act_label,0,2)
        self.RX_grid.addWidget(self.Phase_label,0,3)
        self.RX_grid.addWidget(self.Enc1_label,1,0)
        self.RX_grid.addWidget(self.Enc2_label,1,1)
        self.RX_grid.addWidget(self.Input_label,1,2)
        self.RX_grid.addWidget(self.Dist_label,1,3)
        self.RX_grid.addWidget(self.Linear_label,1,4)

        self.capture_layout=QHBoxLayout()
        self.file_name=QLineEdit()
        self.capture_layout.addWidget(self.file_name)
        self.capture_layout.addStretch(1)
        self.capture_layout.addWidget(self.button_capture)
        self.capture_layout.addWidget(self.button_stop)
        self.capture_layout.addWidget(self.button_plot)
        self.capture_layout.addWidget(self.button_save)

        # 첫 번째 QHBoxLayout 생성
        self.infoBox=QLineEdit('')
        self.infoBox.setReadOnly(True)
        self.info_layout=QHBoxLayout()
        self.info_layout.addWidget(self.infoBox)
        self.info_layout.addWidget(self.button_connect)

        # TabWidget 추가
        self.tabs = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = QWidget()

        # Tab1 구성: 기존 메인 레이아웃을 Tab1으로 이동
        tab1_layout = QVBoxLayout()
        self.configureTab1(tab1_layout)
        self.tab1.setLayout(tab1_layout)

        # Tab2 System Identification
        tab2_layout=QVBoxLayout()
        self.configureTab2(tab2_layout)
        self.tab2.setLayout(tab2_layout)

        # Tabs에 추가
        self.tabs.addTab(self.tab1, "Human Walking Test")
        self.tabs.addTab(self.tab2, "System Identification")

        # 전체 레이아웃
        mainLayout = QVBoxLayout(self)
        mainLayout.addWidget(self.tabs)
        self.setLayout(mainLayout)
        self.setWindowTitle('Flexi-SEA Control GUI')
        self.setGeometry(30, 100, 1200, 800)

    def configureTab1(self, layout):
        hbox1 = QVBoxLayout()
        hbox1.addLayout(self.info_layout)
        hbox1.addWidget(self.rx_title)
        hbox1.addLayout(self.RX_grid)
        hbox1.addLayout(self.capture_layout)
        # 두 번째 QHBoxLayout 생성
        hbox2 = QHBoxLayout()
        # QHBoxLayout에 버튼 추가
        hbox2.addLayout(self.grid)
        hbox2.addLayout(self.layout_ctrl)
        hbox2.addLayout(self.layout_param)

        # Tab1에 추가
        layout.addLayout(hbox1)
        layout.addLayout(hbox2)

    def configureTab2(self, layout):
        # Tab2에 새로운 구성 추가
        hbox=QVBoxLayout()
        hbox.addWidget(self.sysid_infoBox)
        self.sysid_setting_grid=QGridLayout()
        self.sysid_setting_grid.addWidget(self.sysid_freq_min,0,0,1,2)
        self.sysid_setting_grid.addWidget(self.sysid_freq_max,0,2,1,2)
        self.sysid_setting_grid.addWidget(self.sysid_n_sample,1,0,1,2)
        self.sysid_setting_grid.addWidget(self.sysid_n_iter,1,2,1,2)
        self.sysid_setting_grid.addWidget(self.sysid_mag,2,0,1,2)
        self.sysid_setting_grid.addWidget(self.sysid_offset,2,2,1,2)
        self.sysid_setting_grid.addWidget(self.sysid_file_name,3,0,1,3)
        self.sysid_setting_grid.addWidget(self.button_sysid_apply,3,3,1,1)
        self.sysid_setting_grid.addWidget(self.button_sysid_start, 4,1,1,1)
        self.sysid_setting_grid.addWidget(self.button_sysid_stop, 4,2,1,1)
        self.sysid_setting_grid.addWidget(self.button_sysid_save,4,3,1,1)

        layout.addLayout(hbox)
        layout.addLayout(self.sysid_setting_grid)
        # new_label = QLabel('This is Tab 2')
        # new_button = QPushButton('New Button')
        # layout.addWidget(new_label)
        # layout.addWidget(new_button)


    def init_torque(self):
        self.robot_ctrl.init_torque()

    def receive_data(self):
        pass
    def capture_data(self):
        # Sets if trace continue after reaching maximum size for the first file
        self.TraceFileSingle = True
        
        # Set if date will be add to filename
        self.TraceFileDate = True

        # Set if time will be add to filename
        self.TraceFileTime = True

        # Set if existing tracefile overwrites when a new trace session is started
        self.TraceFileOverwrite = False

        # Set if the column "Data Length" should be used instead of the column "Data Length Code"
        self.TraceFileDataLength = False

        # Sets the size (megabyte) of an tracefile 
        # Example - 100 = 100 megabyte
        # Range between 1 and 100
        self.TraceFileSize = 100

        # Sets a fully-qualified and valid path to an existing directory. In order to use the default path 
        # (calling process path) an empty string must be set.
        self.TracePath = b''
        ## ###endregion
        if self.ConfigureTrace():
            if self.StartTrace():
                self.m_objThread = threading.Thread(target = self.ThreadExecute, args = ())
                self.m_ThreadRun = True
                self.m_objThread.start()
                self.infoBox.setText("Messages are being traced.")
                self.button_capture.setChecked(True)
                self.button_stop.setChecked(False)
    def stop_capture(self):
        self.StopTrace()
        self.m_ThreadRun = False
        self.m_objThread.join() 
        self.infoBox.setText('Save Done')
        self.button_capture.setChecked(False)
        self.button_stop.setChecked(True)
        self.load_latest_file()
    def plot_graph(self):
        # 파일 선택 다이얼로그
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getOpenFileName(self, "Select TRC File", "", "TRC Files (*.trc);;All Files (*)", options=options)
        if filename:
            # 선택한 파일 처리 및 시각화 창 열기
            processor = DataProcessor(filename)
            processor.load_data()
            self.show_plot_window(processor.data)
            self.output_filename=self.generate_output_filename(filename)
            self.data=processor.data
    def show_plot_window(self, data):
        # 데이터 시각화를 위한 새 창 열기
        self.plot_window = DataVisualizer(data)
        self.plot_window.show()


    def save_data_to_txt(self):
        # 데이터가 비어있지 않을 때만 저장

        if self.output_filename:
            if any(len(v) > 0 for v in self.data.values()):
                data_array = np.column_stack([
                    self.data['cnt'], self.data['ref_torque'], self.data['force'], self.data['enc1'],
                    self.data['cur'], self.data['ref_vel'],
                    self.data['AC'], self.data['FB'], self.data['mot_vel'], self.data['torque']
                ])
                header = "cnt ref_torque force enc1 cur ref_vel AC FB mot_vel torque"
                np.savetxt(self.output_filename, data_array, header=header, fmt='%.6f', delimiter='\t')
                print(f"Data saved to {self.output_filename}")
            else:
                print("No data to save.")
    def load_latest_file(self):
        # 가장 최근의 .trc 파일 찾기
        folder_path = "./"  # 필요한 폴더 경로 설정
        list_of_files = glob.glob(os.path.join(folder_path, "*.trc"))
        filename = max(list_of_files, key=os.path.getmtime)
        # 데이터 처리 및 시각화 창 열기
        processor = DataProcessor(filename)
        processor.load_data()
        self.show_plot_window(processor.data)
        self.output_filename=self.generate_output_filename(filename)
        self.data=processor.data

    
    def generate_output_filename(self,name):
        # trc 파일의 이름에서 3번째 문자부터 12번째 문자까지 추출
        output_filename = name[:-19]
        if self.PD.isChecked()==True:
            output_filename=output_filename+'_PD'
        if self.FF.isChecked()==True:
            output_filename=output_filename+'_FF'
        if self.DOB.isChecked()==True:
            output_filename=output_filename+'_DOB'
        if self.LS.isChecked()==True:
            output_filename=output_filename+'_LS'
        if self.Fric.isChecked()==True:
            output_filename=output_filename+'_Fric'
        output_filename=output_filename+'_Kp'+self.Kp_label.lineEdit.text()+'_Kd'+self.Kd_label.lineEdit.text()+'_T'+self.Plantar_label.lineEdit.text()
        output_filename=output_filename+'_P'+self.T1_label.lineEdit.text()+'_R'+self.T2_label.lineEdit.text()+'_W'+self.T3_label.lineEdit.text()
        output_filename=output_filename+'.txt'
        print(output_filename)
        return output_filename
    
    def sysid_apply(self):
        min_freq = self.getData(self.sysid_freq_min)
        max_freq = self.getData(self.sysid_freq_max)
        n_sample = self.getData(self.sysid_n_sample)
        n_iter = self.getData(self.sysid_n_iter)
        mag = self.getData(self.sysid_mag)
        offset = self.getData(self.sysid_offset)
        
        self.sysid_ctrl.apply_settings(min_freq, max_freq, n_sample, n_iter, mag, offset)

    def sysid_start(self):
        self.sysid_done = 1
        self.sysid_ctrl.start()
        self.sysid_capture_data()

    def sysid_stop(self):
        self.sysid_done = 0
        self.sysid_ctrl.stop()
        self.sysid_stop_capture()

    def sysid_capture_data(self):
        # Sets if trace continue after reaching maximum size for the first file
        self.TraceFileSingle = True
        self.TraceFileDate = True
        self.TraceFileTime = True
        self.TraceFileOverwrite = False
        self.TraceFileDataLength = False
        self.TraceFileSize = 100
        self.TracePath = b''
        ## ###endregion
        if self.ConfigureTrace():
            if self.StartTrace():
                self.m_objThread = threading.Thread(target = self.ThreadExecute, args = ())
                self.m_ThreadRun = True
                self.m_objThread.start()
                self.sysid_infoBox.setText("Messages are being traced.")
                self.button_sysid_start.setChecked(True)
                self.button_sysid_stop.setChecked(False)

    def sysid_stop_capture(self):
        self.StopTrace()
        self.m_ThreadRun = False
        self.m_objThread.join() 
        self.sysid_infoBox.setText('System ID Done')
        self.button_sysid_start.setChecked(False)
        self.button_sysid_stop.setChecked(True)
        self.sysid_load_latest_file()

    def sysid_save_data_to_txt(self):
        # 데이터가 비어있지 않을 때만 저장
        self.sysid_load_latest_file()
        self.output_filename=self.sysid_file_name.lineEdit.text()
        if self.output_filename:
            if any(len(v) > 0 for v in self.data.values()):
                data_array = np.column_stack([
                    self.data['cnt'], self.data['freq'], self.data['cur'], self.data['force'],
                    self.data['enc1'], self.data['mot_vel']
                ])
                header = "cnt freq cur force enc1 motor_vel"
                np.savetxt(self.output_filename+'.txt', data_array, header=header, fmt='%.6f', delimiter='\t')
                print(f"Data saved to {self.output_filename+'.txt'}")
            else:
                print("No data to save.")
    def sysid_load_latest_file(self):
        # 가장 최근의 .trc 파일 찾기
        folder_path = "./"  # 필요한 폴더 경로 설정
        list_of_files = glob.glob(os.path.join(folder_path, "*.trc"))
        filename = max(list_of_files, key=os.path.getmtime)
        # 데이터 처리 및 시각화 창 열기
        processor = DataProcessor(filename)
        processor.sysid_load_data()
        self.show_plot_window(processor.data)
        self.data=processor.data






    def robot_on(self):
        self.button_roboton.setChecked(True)
        self.button_robotoff.setChecked(False)
        self.robot_ctrl.robot_on(self._get_routine_list, self.getData)

    def robot_off(self):
        self.button_roboton.setChecked(False)
        self.button_robotoff.setChecked(True)
        self.robot_ctrl.robot_off()

    def assist_on(self):
        self.button_assiston.setChecked(True)
        self.button_assistoff.setChecked(False)
        self.robot_ctrl.assist_on()

    def assist_off(self):
        self.button_assiston.setChecked(False)
        self.button_assistoff.setChecked(True)
        self.robot_ctrl.assist_off()

    def test(self):
        self.button_roboton.setChecked(True)
        self.button_robotoff.setChecked(False)
        self.robot_ctrl.test(self._get_routine_list)

    def _get_routine_list(self):
        """Get routine list based on selected options"""
        routine_list = [ROUTINE_ID_MIDLEVEL_RISK_MANAGEMENT]
        
        if self.tabs_ref.currentIndex() == self.tabs_ref.indexOf(self.tab_walking):
            routine_list.extend([ROUTINE_ID_MIDLEVEL_ANKLE_REF])
        if self.tabs_ref.currentIndex() == self.tabs_ref.indexOf(self.tab_sine):
            routine_list.extend([ROUTINE_ID_MIDLEVEL_POSITION_SINE_REF])
        if self.tabs_ref.currentIndex() == self.tabs_ref.indexOf(self.tab_square):
            routine_list.extend([ROUTINE_ID_MIDLEVEL_POSITION_TANH_REF])
        if self.tabs_ref.currentIndex() == self.tabs_ref.indexOf(self.tab_ankle):
            routine_list.extend([ROUTINE_ID_MIDLEVEL_ANKLE_REF_PERIODIC])

        if self.PD.isChecked():
            routine_list.extend([ROUTINE_ID_MIDLEVEL_POSITION_CTRL])
        if self.FF.isChecked():
            routine_list.extend([ROUTINE_ID_MIDLEVEL_FEEDFORWARD_FILTER])
        if self.DOB.isChecked():
            routine_list.extend([ROUTINE_ID_MIDLEVEL_DISTURBANCE_OBS])
        if self.LS.isChecked():
            routine_list.extend([ROUTINE_ID_MIDLEVEL_VELOCITY_CTRL])
        if self.Fric.isChecked():
            routine_list.extend([ROUTINE_ID_MIDLEVEL_ANKLE_COMPENSATOR])
        
        return routine_list
    

    def set_ctrl(self):
        Max_error = self.getData(self.Max_error)
        Max_ROM = self.getData(self.Max_ank_ang)
        Min_ROM = self.getData(self.Min_ank_ang)

        msg = [1, pack_sdo_unit(TASK_ID_MIDLEVEL, SDO_ID_MIDLEVEL_RISK_PARAM, SDO_REQU, 3, 
                               [float_to_byte_list(Max_error), float_to_byte_list(Max_ROM), float_to_byte_list(Min_ROM)])]
        msg = flatten_list(msg)
        self.pcan_comm.send_message(msg, SDO, self.node_id)
        
        Kp = self.getData(self.Kp_label)
        Kd = self.getData(self.Kd_label)
        sat = self.getData(self.Limit_label)

        msg = [3, pack_sdo_unit(TASK_ID_MIDLEVEL, SDO_ID_MIDLEVEL_POSITION_CTRL_P_GAIN, SDO_REQU, 1, float_to_byte_list(Kp)), 
               pack_sdo_unit(TASK_ID_MIDLEVEL, SDO_ID_MIDLEVEL_POSITION_CTRL_D_GAIN, SDO_REQU, 1, float_to_byte_list(Kd)),
               pack_sdo_unit(TASK_ID_MIDLEVEL, SDO_ID_MIDLEVEL_MID_CTRL_SATURATION, SDO_REQU, 1, float_to_byte_list(sat))]
        msg = flatten_list(msg)
        self.pcan_comm.send_message(msg, SDO, self.node_id)

        imp_kp = self.getData(self.imp_kp_label)
        imp_kd = self.getData(self.imp_kd_label)
        imp_lambda = self.getData(self.imp_lambda_label)
        imp_epsilon = self.getData(self.imp_epsilon_label)

        msg = [1, pack_sdo_unit(TASK_ID_MIDLEVEL, SDO_ID_MIDLEVEL_IMPEDANCECTRL_INFO, SDO_REQU, 4, 
               [float_to_byte_list(imp_kp), float_to_byte_list(imp_kd), float_to_byte_list(imp_lambda), float_to_byte_list(imp_epsilon)])]
        msg = flatten_list(msg)
        self.pcan_comm.send_message(msg, SDO, self.node_id)


        
    def getData(self, label):
        result=label.lineEdit.text()
        if result =='': result=0
        else: result=float(result)
        return result
    
    def set_param(self):
        if self.tabs_ref.currentIndex() == self.tabs_ref.indexOf(self.tab_walking):
            plantar_amp = self.getData(self.Plantar_label)
            dorsi_amp = self.getData(self.Dorsi_label)
            dorsi_amp2 = self.getData(self.Dorsi_label2)
            T1 = self.getData(self.T1_label)
            T2 = self.getData(self.T2_label)
            T3 = self.getData(self.T3_label)
            T4 = self.getData(self.T4_label)
            T5 = self.getData(self.T5_label)
            T6 = self.getData(self.T6_label)
            T7 = self.getData(self.T7_label)
            phase_shift = self.getData(self.phase_shift_label)
            plantar_init = float(format(T1 - T2 * T3, ".2f"))
            plantar_terminal = float(format(T1 + T2 * T3, ".2f"))
            self.plantar_init_label.lineEdit.setText(str(plantar_init))
            self.plantar_terminal_label.lineEdit.setText(str(plantar_terminal))
            msg = [1, pack_sdo_unit(TASK_ID_MIDLEVEL, SDO_ID_MIDLEVEL_ANKLE_REF_INFO, SDO_REQU, 4, 
                   [float_to_byte_list(plantar_amp), float_to_byte_list(T1), float_to_byte_list(T2), float_to_byte_list(T3)])]
            msg = flatten_list(msg)
            self.pcan_comm.send_message(msg, SDO, self.node_id)

            msg = [1, pack_sdo_unit(TASK_ID_MIDLEVEL, SDO_ID_MIDLEVEL_ANKLE_REF_INFO2, SDO_REQU, 4, 
                   [float_to_byte_list(dorsi_amp), float_to_byte_list(dorsi_amp2), float_to_byte_list(T4), float_to_byte_list(T5)])]
            msg = flatten_list(msg)
            self.pcan_comm.send_message(msg, SDO, self.node_id)

            msg = [1, pack_sdo_unit(TASK_ID_MIDLEVEL, SDO_ID_MIDLEVEL_ANKLE_REF_INFO3, SDO_REQU, 2, 
                   [float_to_byte_list(T6), float_to_byte_list(T7)])]
            msg = flatten_list(msg)
            self.pcan_comm.send_message(msg, SDO, self.node_id)

            msg = [1, pack_sdo_unit(TASK_ID_MIDLEVEL, SDO_ID_MIDLEVEL_PHASE_SHIFT, SDO_REQU, 1, float_to_byte_list(phase_shift))]
            msg = flatten_list(msg)
            self.pcan_comm.send_message(msg, SDO, self.node_id)
            
        if self.tabs_ref.currentIndex() == self.tabs_ref.indexOf(self.tab_sine):
            amp = self.getData(self.refsine_amp_label)
            freq = self.getData(self.refsine_freq_label)
            msg = [1, pack_sdo_unit(TASK_ID_MIDLEVEL, SDO_ID_MIDLEVEL_POSITION_PERIODIC_SIG_INFO, SDO_REQU, 3, 
                   [float_to_byte_list(amp), float_to_byte_list(freq), float_to_byte_list(0)])]
            msg = flatten_list(msg)
            self.pcan_comm.send_message(msg, SDO, self.node_id)
            
        if self.tabs_ref.currentIndex() == self.tabs_ref.indexOf(self.tab_square):
            amp = self.getData(self.reftanh_amp_label)
            a = self.getData(self.reftanh_a_label)
            td = self.getData(self.reftanh_td_label)
            msg = [1, pack_sdo_unit(TASK_ID_MIDLEVEL, SDO_ID_MIDLEVEL_POSITION_TANH_INFO, SDO_REQU, 3, 
                   [float_to_byte_list(amp), float_to_byte_list(a), float_to_byte_list(td)])]
            msg = flatten_list(msg)
            self.pcan_comm.send_message(msg, SDO, self.node_id)
            
        if self.tabs_ref.currentIndex() == self.tabs_ref.indexOf(self.tab_ankle):
            plantar_amp = self.getData(self.refAnkle_amp_label)
            peak = self.getData(self.refAnkle_peak_label)
            ratio = self.getData(self.refAnkle_ratio_label)
            width = self.getData(self.refAnkle_width_label)
            msg = [1, pack_sdo_unit(TASK_ID_MIDLEVEL, SDO_ID_MIDLEVEL_ANKLE_REF_INFO, SDO_REQU, 4, 
                   [float_to_byte_list(plantar_amp), float_to_byte_list(peak), float_to_byte_list(ratio), float_to_byte_list(width)])]
            msg = flatten_list(msg)
            self.pcan_comm.send_message(msg, SDO, self.node_id)
        
    def shift_right(self):
        T1=self.getData(self.T1_label)
        T2=self.getData(self.T2_label)
        T3=self.getData(self.T3_label)
        T4=self.getData(self.T4_label)
        T5=self.getData(self.T5_label)
        T6=self.getData(self.T6_label)
        self.T1_label.lineEdit.setText(str(T1+1))
        self.T2_label.lineEdit.setText(str(T2+1))
        self.T3_label.lineEdit.setText(str(T3+1))
        self.T4_label.lineEdit.setText(str(T4+1))
        self.T5_label.lineEdit.setText(str(T5+1))
        self.T6_label.lineEdit.setText(str(T6+1))

    def shift_left(self):
        T1=self.getData(self.T1_label)
        T2=self.getData(self.T2_label)
        T3=self.getData(self.T3_label)
        T4=self.getData(self.T4_label)
        T5=self.getData(self.T5_label)
        T6=self.getData(self.T6_label)
        self.T1_label.lineEdit.setText(str(T1-1))
        self.T2_label.lineEdit.setText(str(T2-1))
        self.T3_label.lineEdit.setText(str(T3-1))
        self.T4_label.lineEdit.setText(str(T4-1))
        self.T5_label.lineEdit.setText(str(T5-1))
        self.T6_label.lineEdit.setText(str(T6-1))


    def connect(self):
        if self.pcan_comm.initialize():
            self.infoBox.setText("Successfully initialized.")
        else:
            self.infoBox.setText("Failed to initialize PCAN.")


    # Main-Functions
    #region
    def ThreadExecute(self):
        '''
        Thread function for reading messages
        '''
        while self.m_ThreadRun:
            ## time.sleep(1) ## Use Sleep to reduce the CPU load   
            self.ReadMessages()
            # if self.sysid_done==2:
            #     print('system id done')
            #     self.sysid_stop_capture()
    def ReadMessages(self):
        """
        Reads PCAN-Basic messages
        """
        stsResult = [PCAN_ERROR_OK]
        ## We read at least one time the queue looking for messages. If a message is found, we look again trying to find more.
        ## If the queue is empty or an error occurr, we get out from the while statement.
        while stsResult[0] != PCAN_ERROR_QRCVEMPTY:
            if self.IsFD:
                stsResult = self.m_objPCANBasic.ReadFD(self.PcanHandle)

            if stsResult[0] != PCAN_ERROR_OK and stsResult[0] != PCAN_ERROR_QRCVEMPTY:
                self.ShowStatus(stsResult[0])
                break
            msg=stsResult[1]
            # self.showData(msg.DATA, msg.ID)

    def StopTrace(self):
        """
        Deactivates the tracing process
        """
        ## We stop the tracing by setting the parameter.
        stsResult = self.m_objPCANBasic.SetValue(self.PcanHandle,PCAN_TRACE_STATUS, PCAN_PARAMETER_OFF)
        if stsResult != PCAN_ERROR_OK:
            self.ShowStatus(stsResult)
        else:
            self.ThreadRun = False

    def ConfigureTrace(self):
        """
        Configures the way how trace files are formatted
        """
        stsResult = self.m_objPCANBasic.SetValue(self.PcanHandle,PCAN_TRACE_LOCATION, self.TracePath) ## Sets path to store files
        if stsResult == PCAN_ERROR_OK:

            stsResult = self.m_objPCANBasic.SetValue(self.PcanHandle,PCAN_TRACE_SIZE, self.TraceFileSize) ## Sets the maximum size of file
            if (stsResult == PCAN_ERROR_OK):
                
                if (self.TraceFileSingle):
                    config = TRACE_FILE_SINGLE ## Creats one file
                else:
                    config = TRACE_FILE_SEGMENTED ## Creats more files

                ## Overwrites existing tracefile
                if self.TraceFileOverwrite:
                    config = config | TRACE_FILE_OVERWRITE

                ## Uses Data Length instead of Data Length Code
                if self.TraceFileDataLength:
                    config = config | TRACE_FILE_DATA_LENGTH
                
                ## Adds date to tracefilename
                if self.TraceFileDate:
                    config = config | TRACE_FILE_DATE

                 ## Adds time to tracefilename
                if self.TraceFileTime:
                    config = config | TRACE_FILE_TIME

                stsResult = self.m_objPCANBasic.SetValue(self.PcanHandle,PCAN_TRACE_CONFIGURE, config)
                if (stsResult == PCAN_ERROR_OK):
                    return True
        self.ShowStatus(stsResult)
        return False

    def StartTrace(self):
        """
        Activates the tracing process
        """
        ## We activate the tracing by setting the parameter.
        stsResult = self.m_objPCANBasic.SetValue(self.PcanHandle, PCAN_TRACE_STATUS, PCAN_PARAMETER_ON)
        if stsResult != PCAN_ERROR_OK:
            self.ShowStatus(stsResult)
            return False
        self.ThreadRun = True
        return True
    #endregion

    def ShowStatus(self,status):
        """
        Shows formatted status

        Parameters:
            status = Will be formatted
        """
        print("=========================================================================================")
        print(self.GetFormattedError(status))
        print("=========================================================================================")
    def ShowCurrentConfiguration(self):
        """
        Shows/prints the configured paramters
        """
        print("Parameter values used")
        print("----------------------")
        print("* PCANHandle: " + self.FormatChannelName(self.PcanHandle))
        print("* IsFD: " + str(self.IsFD))
        print("* Bitrate: " + self.ConvertBitrateToString(self.Bitrate))
        print("* BitrateFD: " + self.ConvertBytesToString(self.BitrateFD))
        print("* TraceFileSingle: " + str(self.TraceFileSingle))
        print("* TraceFileDate: " + str(self.TraceFileDate))
        print("* TraceFileTime: " + str(self.TraceFileTime))
        print("* TraceFileOverwrite: " + str(self.TraceFileOverwrite))
        print("* TraceFileDataLength: " + str(self.TraceFileDataLength))
        print("* TraceFileSize: " + str(self.TraceFileSize) + " MB")
        if self.TracePath == b'':
            print("* TracePath: (calling application path)")
        else:
            print("* TracePath: " + self.ConvertBytesToString(self.TracePath))
        print("")

    def ShowStatus(self,status):
        """
        Shows formatted status

        Parameters:
            status = Will be formatted
        """
        print("=========================================================================================")
        print(self.GetFormattedError(status))
        print("=========================================================================================")
    
    def FormatChannelName(self, handle, isFD=False):
        """
        Gets the formated text for a PCAN-Basic channel handle

        Parameters:
            handle = PCAN-Basic Handle to format
            isFD = If the channel is FD capable

        Returns:
            The formatted text for a channel
        """
        handleValue = handle.value
        if handleValue < 0x100:
            devDevice = TPCANDevice(handleValue >> 4)
            byChannel = handleValue & 0xF
        else:
            devDevice = TPCANDevice(handleValue >> 8)
            byChannel = handleValue & 0xFF

        if isFD:
           return ('%s:FD %s (%.2Xh)' % (self.GetDeviceName(devDevice.value), byChannel, handleValue))
        else:
           return ('%s %s (%.2Xh)' % (self.GetDeviceName(devDevice.value), byChannel, handleValue))

    def GetFormattedError(self, error):
        """
        Help Function used to get an error as text

        Parameters:
            error = Error code to be translated

        Returns:
            A text with the translated error
        """
        ## Gets the text using the GetErrorText API function. If the function success, the translated error is returned.
        ## If it fails, a text describing the current error is returned.
        stsReturn = self.m_objPCANBasic.GetErrorText(error,0x09)
        if stsReturn[0] != PCAN_ERROR_OK:
            return "An error occurred. Error-code's text ({0:X}h) couldn't be retrieved".format(error)
        else:
            message = str(stsReturn[1])
            return message.replace("'","",2).replace("b","",1)
      
    def GetDeviceName(self, handle):
        """
        Gets the name of a PCAN device

        Parameters:
            handle = PCAN-Basic Handle for getting the name

        Returns:
            The name of the handle
        """
        switcher = {
            PCAN_NONEBUS.value: "PCAN_NONEBUS",
            PCAN_PEAKCAN.value: "PCAN_PEAKCAN",
            PCAN_DNG.value: "PCAN_DNG",
            PCAN_PCI.value: "PCAN_PCI",
            PCAN_USB.value: "PCAN_USB",
            PCAN_VIRTUAL.value: "PCAN_VIRTUAL",
            PCAN_LAN.value: "PCAN_LAN"
        }

        return switcher.get(handle,"UNKNOWN")   

    def ConvertBitrateToString(self, bitrate):
        """
        Convert bitrate c_short value to readable string

        Parameters:
            bitrate = Bitrate to be converted

        Returns:
            A text with the converted bitrate
        """
        m_BAUDRATES = {PCAN_BAUD_1M.value:'1 MBit/sec', PCAN_BAUD_800K.value:'800 kBit/sec', PCAN_BAUD_500K.value:'500 kBit/sec', PCAN_BAUD_250K.value:'250 kBit/sec',
                       PCAN_BAUD_125K.value:'125 kBit/sec', PCAN_BAUD_100K.value:'100 kBit/sec', PCAN_BAUD_95K.value:'95,238 kBit/sec', PCAN_BAUD_83K.value:'83,333 kBit/sec',
                       PCAN_BAUD_50K.value:'50 kBit/sec', PCAN_BAUD_47K.value:'47,619 kBit/sec', PCAN_BAUD_33K.value:'33,333 kBit/sec', PCAN_BAUD_20K.value:'20 kBit/sec',
                       PCAN_BAUD_10K.value:'10 kBit/sec', PCAN_BAUD_5K.value:'5 kBit/sec'}
        return m_BAUDRATES[bitrate.value]

    def ConvertBytesToString(self, bytes):
        """
        Convert bytes value to string

        Parameters:
            bytes = Bytes to be converted

        Returns:
            Converted bytes value as string
        """
        return str(bytes).replace("'","",2).replace("b","",1)
    
    def ProcessMessageCanFd(self,msg,itstimestamp):
        """
        Processes a received CAN-FD message

        Parameters:
            msg = The received PCAN-Basic CAN-FD message
            itstimestamp = Timestamp of the message as microseconds (ulong)
        """
        # print("Type: " + self.GetTypeString(msg.MSGTYPE))
        # print("ID: " + self.GetIdString(msg.ID, msg.MSGTYPE))
        # print("Type: " + str(self.GetLengthFromDLC(msg.DLC)))
        # print("Type: " + self.GetTimeString(itstimestamp))
        # print("Type: " + self.GetDataString(msg.DATA,msg.MSGTYPE))
        # print("----------------------------------------------------------")
        # self.infoBox.setText(self.GetDataString(msg.DATA,msg.MSGTYPE))
        self.showData(msg.DATA, msg.MSGTYPE, msg.ID)
    # #endregion
    def GetLengthFromDLC(dlc):
        """
        Gets the data length of a CAN message

        Parameters:
            dlc = Data length code of a CAN message

        Returns:
            Data length as integer represented by the given DLC code
        """
        if dlc == 9:
            return 12
        elif dlc == 10:
            return 16
        elif dlc == 11:
            return 20
        elif dlc == 12:
            return 24
        elif dlc == 13:
            return 32
        elif dlc == 14:
            return 48
        elif dlc == 15:
            return 64
        
        return dlc

    def GetIdString(self, id, msgtype):
        """
        Gets the string representation of the ID of a CAN message

        Parameters:
            id = Id to be parsed
            msgtype = Type flags of the message the Id belong

        Returns:
            Hexadecimal representation of the ID of a CAN message
        """
        if (msgtype & PCAN_MESSAGE_EXTENDED.value) == PCAN_MESSAGE_EXTENDED.value:
            return '%.8Xh' %id
        else:
            return '%.3Xh' %id

    def GetTimeString(self, time):
        """
        Gets the string representation of the timestamp of a CAN message, in milliseconds

        Parameters:
            time = Timestamp in microseconds

        Returns:
            String representing the timestamp in milliseconds
        """
        fTime = time / 1000.0
        return '%.1f' %fTime

    def GetTypeString(self, msgtype):  
        """
        Gets the string representation of the type of a CAN message

        Parameters:
            msgtype = Type of a CAN message

        Returns:
            The type of the CAN message as string
        """
        if (msgtype & PCAN_MESSAGE_STATUS.value) == PCAN_MESSAGE_STATUS.value:
            return 'STATUS'
        
        if (msgtype & PCAN_MESSAGE_ERRFRAME.value) == PCAN_MESSAGE_ERRFRAME.value:
            return 'ERROR'        
        
        if (msgtype & PCAN_MESSAGE_EXTENDED.value) == PCAN_MESSAGE_EXTENDED.value:
            strTemp = 'EXT'
        else:
            strTemp = 'STD'

        if (msgtype & PCAN_MESSAGE_RTR.value) == PCAN_MESSAGE_RTR.value:
            strTemp += '/RTR'
        else:
            if (msgtype > PCAN_MESSAGE_EXTENDED.value):
                strTemp += ' ['
                if (msgtype & PCAN_MESSAGE_FD.value) == PCAN_MESSAGE_FD.value:
                    strTemp += ' FD'
                if (msgtype & PCAN_MESSAGE_BRS.value) == PCAN_MESSAGE_BRS.value:                    
                    strTemp += ' BRS'
                if (msgtype & PCAN_MESSAGE_ESI.value) == PCAN_MESSAGE_ESI.value:
                    strTemp += ' ESI'
                strTemp += ' ]'
                
        return strTemp

    def GetDataString(self, data, msgtype):
        """
        Gets the data of a CAN message as a string

        Parameters:
            data = Array of bytes containing the data to parse
            msgtype = Type flags of the message the data belong

        Returns:
            A string with hexadecimal formatted data bytes of a CAN message
        """
        if (msgtype & PCAN_MESSAGE_RTR.value) == PCAN_MESSAGE_RTR.value:
            return "Remote Request"
        else:
            strTemp = b""
            for x in data:
                strTemp += b'%.2X ' % x
            return str(strTemp).replace("'","",2).replace("b","",1)

    def showData(self, data, id):
        if self.sysid_done ==0:
            if id==0x371:
                strTemp = b""
                for x in data:
                    strTemp += b'%.2X ' % x
                # print(strTemp)
                recv_buffer = bytes.fromhex(strTemp.decode('utf-8'))
                data1=struct.unpack('f', bytes(recv_buffer[3:7]))[0]
                data2=struct.unpack('f', bytes(recv_buffer[9:13]))[0]
                data3=struct.unpack('f', bytes(recv_buffer[15:19]))[0]
                # data4=struct.unpack('f', bytes(recv_buffer[21:25]))[0]
                # data5=struct.unpack('f', bytes(recv_buffer[27:31]))[0]
                # data6=struct.unpack('f', bytes(recv_buffer[33:37]))[0]
                # data7=struct.unpack('f', bytes(recv_buffer[39:43]))[0]
                # data8=struct.unpack('f', bytes(recv_buffer[45:49]))[0]
                data9=struct.unpack('f', bytes(recv_buffer[51:55]))[0]
                # data10=struct.unpack('f', bytes(recv_buffer[57:61]))[0]
                print(f"cnt={data1}, ref={data2}, act={data3},phase={data9}")
                print("------------------------------------------------------")
                # self.Cnt_label.lineEdit.setText(f"{data1}")
                # self.Ref_label.lineEdit.setText(f"{data2}")
                # self.Act_label.lineEdit.setText(f"{data3}")
                # self.Enc1_label.lineEdit.setText(f"{data4}")
                # self.Enc2_label.lineEdit.setText(f"{data5}")
                # self.Input_label.lineEdit.setText(f"{data9}")
                # self.Dist_label.lineEdit.setText(f"{data6}")
                # self.Linear_label.lineEdit.setText(f"{data8}")
                # self.Phase_label.lineEdit.setText(f"{data10}")
        elif self.sysid_done == 1:
            if id==0x371:
                strTemp = b""
                for x in data:
                    strTemp += b'%.2X ' % x
                # print(strTemp)
                recv_buffer = bytes.fromhex(strTemp.decode('utf-8'))
                freq = struct.unpack('<f', recv_buffer[9:13])[0]
                cnt = struct.unpack('<i', recv_buffer[21:25])[0]
                done = struct.unpack('<i', recv_buffer[39:43])[0]
                print(f"cnt={cnt}, freq={freq}, done={done}")
                print("------------------------------------------------------")
                if done == 1:
                    self.trigger_stop_sysid.emit()

    def __del__(self):
        self.pcan_comm.uninitialize()
# 코드 실행
if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = GUI()
    gui.show()
    sys.exit(app.exec_())