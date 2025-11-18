"""
UI Builder - constructs and configures UI components and layouts
"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from ui_widgets import TitleLabel, TextLabel, LabeledLineEdit


# For backward compatibility
lb = LabeledLineEdit


class UIBuilder:
    """UI 컴포넌트 생성 및 레이아웃 구성"""
    
    def __init__(self):
        """UI 컴포넌트 초기화"""
        self.buttons = {}
        self.labels = {}
        self.layouts = {}
        self.tabs = {}
        self.checkboxes = {}
        self.other_widgets = {}

    def create_buttons(self):
        """모든 버튼 생성"""
        button_config = {
            'inittorque': ('Initiate Torque', 'black', True, None),
            'roboton': ('Robot On', 'blue', True, (150, 50)),
            'assiston': ('Assist On', 'blue', True, (150, 50)),
            'robotoff': ('Robot Off', 'red', True, (150, 50)),
            'assistoff': ('Assist Off', 'red', True, (150, 50)),
            'capture': ('CAPTURE', 'black', False, (150, 50)),
            'stop': ('STOP', 'red', False, (150, 50)),
            'plot': ('PLOT', 'blue', False, (150, 50)),
            'save': ('SAVE', 'blue', False, (150, 50)),
            'setCtrl': ('SET', 'black', False, (150, 50)),
            'setParam': ('SET PARAMETER', 'black', False, (200, 50)),
            'shiftright': ('->', 'black', False, (100, 50)),
            'shiftleft': ('<-', 'black', False, (100, 50)),
            'connect': ('TEST', 'black', False, (150, 50)),
            'sysid_start': ('Start ID', 'black', False, (150, 50)),
            'sysid_stop': ('Stop ID', 'red', False, (150, 50)),
            'sysid_apply': ('Apply', 'black', False, (150, 50)),
            'sysid_save': ('SAVE', 'blue', False, (150, 50)),
        }
        
        for key, (text, color, expanding, size) in button_config.items():
            btn = QPushButton(text)
            btn.setStyleSheet(f"background-color: {color}; color: white; font-size: 12pt; font-weight: bold;")
            
            if expanding:
                btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            elif size:
                btn.setFixedSize(*size)
            
            self.buttons[key] = btn
        
        return self.buttons

    def create_labels(self):
        """모든 라벨 생성"""
        label_config = {
            'Cnt': ('Count(ms):', 0),
            'Ref': ('Ref(Nm):', 0),
            'Act': ('Act(Nm):', 0),
            'Phase': ('Phase(%):', 0),
            'Enc1': ('Enc1(deg):', 0),
            'Enc2': ('Enc2(deg):', 0),
            'Input': ('Input(A):', 0),
            'Dist': ('Dist(A):', 0),
            'Linear': ('Linear(A):', 0),
            'Limit': ('Limit(A):', 6),
            'Plantar': ('Plantar Amp(Nm):', 5),
            'Dorsi': ('Dorsi peak(deg):', 5),
            'Dorsi2': ('Dorsi terminal(deg):', 0),
            'T1': ('Peak Time(%):', 55),
            'T2': ('Ratio :', 0.714),
            'T3': ('Width(%):', 60),
            'T4': ('Peak Duration(%):', 0),
            'T5': ('Dorsi Initial(%):', 0),
            'T6': ('Peak(%):', 0),
            'T7': ('Terminal(%):', 0),
            'Kp': ('Kp:', 0.2),
            'Kd': ('Kd:', 0.0001),
            'plantar_init': ('Plantar Init(%):', 0),
            'plantar_terminal': ('Terminal(%):', 0),
            'imp_kp': ('Kp:', 11.73),
            'imp_kd': ('Kd:', 0.83),
            'imp_lambda': ('lambda:', 0),
            'imp_epsilon': ('epsilon:', 0),
            'Max_error': ('Maximum Error(N):', 30),
            'Max_ank_ang': ('Max(D)(deg):', 20),
            'Min_ank_ang': ('ROM Min(P) (deg):', -35),
            'reftanh_amp': ('Amplitude (Nm):', 5),
            'reftanh_a': ('a:', 10),
            'reftanh_td': ('duration(s):', 1),
            'refsine_amp': ('Amplitude (Nm):', 5),
            'refsine_freq': ('Frequency (Hz):', 1),
            'refAnkle_amp': ('Plantar Amp(Nm):', 5),
            'refAnkle_peak': ('Peak Time(%):', 55),
            'refAnkle_ratio': ('Ratio :', 0.6),
            'refAnkle_width': ('Width(%):', 60),
            'refAnkle_gaitperiod': ('Gait Period (ms):', 2000),
            'phase_shift': ('Phase Shift (%):', 0),
            'sysid_freq_min': ('Minimum Freq (Hz):', 0.2),
            'sysid_freq_max': ('Maximum Freq (Hz):', 2),
            'sysid_n_sample': ('Number of Freq:', 5),
            'sysid_n_iter': ('Number of iteration:', 5),
            'sysid_mag': ('Input Magnitude (A)', 0),
            'sysid_offset': ('Input Offset', 0),
            'sysid_file_name': ('File Save Name (.txt)', "250304_Flexi_Ankle_ID"),
            'saan_k_torque': ('K_torque:', 0),
            'saan_max_torque': ('Max Torque:', 0),
            'saan_power_PF': ('Power PF:', 1),
            'saan_power_DF': ('Power DF:', 1),
        }
        
        for key, (text, value) in label_config.items():
            label = lb(text, value)
            self.labels[key] = label
            
            # Read-only labels
            if key in ['plantar_init', 'plantar_terminal']:
                label.lineEdit.setReadOnly(True)
        
        return self.labels

    def create_checkboxes(self):
        """모든 체크박스 생성"""
        checkbox_config = {
            'PD': True,
            'DOB': False,
            'FF': False,
            'LS': True,
            'Fric': False,
        }
        
        for key, checked in checkbox_config.items():
            cb = QCheckBox(key if key != 'LS' else 'vel_ctrl' if key == 'LS' else 'Ankle_Comp' if key == 'Fric' else key)
            if key == 'LS':
                cb.setText('vel_ctrl')
            elif key == 'Fric':
                cb.setText('Ankle_Comp')
            cb.setChecked(checked)
            self.checkboxes[key] = cb
        
        return self.checkboxes

    def create_node_selection(self):
        """MD 노드 선택 라디오 버튼 생성"""
        selection_widget = QWidget()
        layout = QHBoxLayout(selection_widget)
        
        # 라벨
        label = QLabel("Select MD:")
        layout.addWidget(label)
        
        # 라디오 버튼 그룹
        button_group = QButtonGroup()
        
        # LEFT 라디오 버튼 (0x06)
        rb_left = QRadioButton("LEFT (0x06)")
        rb_left.setChecked(False)
        button_group.addButton(rb_left, 0x06)
        layout.addWidget(rb_left)
        
        # RIGHT 라디오 버튼 (0x07)
        rb_right = QRadioButton("RIGHT (0x07)")
        rb_right.setChecked(True)
        button_group.addButton(rb_right, 0x07)
        layout.addWidget(rb_right)
        
        layout.addStretch()
        
        self.other_widgets['node_selection'] = selection_widget
        self.other_widgets['node_button_group'] = button_group
        self.other_widgets['rb_left'] = rb_left
        self.other_widgets['rb_right'] = rb_right
        
        return selection_widget

    def create_title_labels(self):
        """제목 라벨 생성"""
        self.other_widgets['rx_title'] = TitleLabel('Data Acquisition')
        self.other_widgets['ctrl_title'] = TitleLabel('Controller Setting')
        self.other_widgets['param_title'] = TitleLabel('Parameter Setting')
        self.other_widgets['imp_ctrl_title'] = TitleLabel('Impedance Setting')
        self.other_widgets['sysid_infoBox'] = QLineEdit('')
        self.other_widgets['sysid_infoBox'].setReadOnly(True)
        self.other_widgets['infoBox'] = QLineEdit('')
        self.other_widgets['infoBox'].setReadOnly(True)
        self.other_widgets['file_name'] = QLineEdit()
        
        return self.other_widgets

    def build_controller_layout(self):
        """컨트롤러 설정 레이아웃 구성"""
        layout = QGridLayout()
        layout.addWidget(self.other_widgets['ctrl_title'], 0, 0, 1, 2)
        layout.addWidget(self.checkboxes['PD'], 1, 0)
        layout.addWidget(self.checkboxes['DOB'], 1, 1)
        layout.addWidget(self.checkboxes['FF'], 2, 0)
        layout.addWidget(self.checkboxes['LS'], 2, 1)
        layout.addWidget(self.checkboxes['Fric'], 3, 0)
        layout.addWidget(self.labels['Limit'], 4, 0, 1, 2)
        layout.addWidget(self.labels['Kp'], 5, 0)
        layout.addWidget(self.labels['Kd'], 5, 1)
        layout.addWidget(self.labels['Max_error'], 6, 0)
        layout.addWidget(self.labels['Min_ank_ang'], 7, 0)
        layout.addWidget(self.labels['Max_ank_ang'], 7, 1)
        layout.addWidget(self.other_widgets['imp_ctrl_title'], 8, 0, 1, 2)
        layout.addWidget(self.labels['imp_kp'], 9, 0)
        layout.addWidget(self.labels['imp_kd'], 9, 1)
        layout.addWidget(self.labels['imp_lambda'], 10, 0)
        layout.addWidget(self.labels['imp_epsilon'], 10, 1)
        layout.addWidget(self.buttons['setCtrl'], 11, 0, 1, 2)
        
        return layout

    def build_parameter_layout(self):
        """파라미터 설정 레이아웃 구성"""
        layout = QVBoxLayout()
        
        # Walking tab
        grid_walking = QGridLayout()
        grid_walking.addWidget(self.labels['Plantar'], 0, 0, 1, 2)
        grid_walking.addWidget(self.labels['T1'], 1, 1)
        grid_walking.addWidget(self.labels['plantar_init'], 1, 0)
        grid_walking.addWidget(self.labels['plantar_terminal'], 1, 2)
        grid_walking.addWidget(self.labels['T2'], 2, 0)
        grid_walking.addWidget(self.labels['T3'], 2, 1)
        grid_walking.addWidget(self.labels['T4'], 2, 2)
        grid_walking.addWidget(self.labels['Dorsi'], 3, 0)
        grid_walking.addWidget(self.labels['Dorsi2'], 3, 1)
        grid_walking.addWidget(self.labels['T5'], 4, 0)
        grid_walking.addWidget(self.labels['T6'], 4, 1)
        grid_walking.addWidget(self.labels['T7'], 4, 2)
        grid_walking.addWidget(self.labels['phase_shift'], 5, 0)
        
        # Sine tab
        layout_sine = QVBoxLayout()
        layout_sine.addWidget(self.labels['refsine_amp'])
        layout_sine.addWidget(self.labels['refsine_freq'])
        
        # Square (Tanh) tab
        layout_tanh = QVBoxLayout()
        layout_tanh.addWidget(self.labels['reftanh_amp'])
        layout_tanh.addWidget(self.labels['reftanh_a'])
        layout_tanh.addWidget(self.labels['reftanh_td'])
        
        # Ankle tab
        layout_ankle = QVBoxLayout()
        layout_ankle.addWidget(self.labels['refAnkle_amp'])
        layout_ankle.addWidget(self.labels['refAnkle_peak'])
        layout_ankle.addWidget(self.labels['refAnkle_ratio'])
        layout_ankle.addWidget(self.labels['refAnkle_width'])
        layout_ankle.addWidget(self.labels['refAnkle_gaitperiod'])
        
        # SAAN tab
        layout_saan = QVBoxLayout()
        layout_saan.addWidget(self.labels['saan_k_torque'])
        layout_saan.addWidget(self.labels['saan_max_torque'])
        layout_saan.addWidget(self.labels['saan_power_PF'])
        layout_saan.addWidget(self.labels['saan_power_DF'])
        
        # Tabs
        tabs_ref = QTabWidget()
        tab_walking = QWidget()
        tab_sine = QWidget()
        tab_square = QWidget()
        tab_ankle = QWidget()
        tab_saan = QWidget()
        tab_walking.setLayout(grid_walking)
        tab_sine.setLayout(layout_sine)
        tab_square.setLayout(layout_tanh)
        tab_ankle.setLayout(layout_ankle)
        tab_saan.setLayout(layout_saan)
        tabs_ref.addTab(tab_walking, "Walking")
        tabs_ref.addTab(tab_sine, "Sine")
        tabs_ref.addTab(tab_square, "Square")
        tabs_ref.addTab(tab_ankle, "Ankle")
        tabs_ref.addTab(tab_saan, "SAAN")
        
        layout.addWidget(self.other_widgets['param_title'])
        layout.addStretch(1)
        layout.addWidget(tabs_ref)
        layout.addStretch(1)
        
        layout_button = QHBoxLayout()
        layout_button.addWidget(self.buttons['setParam'])
        layout_button.addWidget(self.buttons['shiftleft'])
        layout_button.addWidget(self.buttons['shiftright'])
        layout_button.addStretch()
        layout.addLayout(layout_button)
        
        self.tabs['ref'] = tabs_ref
        self.tabs['walking'] = tab_walking
        self.tabs['sine'] = tab_sine
        self.tabs['square'] = tab_square
        self.tabs['ankle'] = tab_ankle
        self.tabs['saan'] = tab_saan
        
        return layout, tabs_ref

    def build_tab1_layout(self):
        """Tab 1 (Human Walking Test) 레이아웃"""
        layout = QVBoxLayout()
        
        # Info box
        info_layout = QHBoxLayout()
        info_layout.addWidget(self.other_widgets['infoBox'])
        info_layout.addWidget(self.buttons['connect'])
        
        # Data acquisition section
        layout.addLayout(info_layout)
        layout.addWidget(self.other_widgets['rx_title'])
        
        # RX grid
        rx_grid = QGridLayout()
        rx_grid.addWidget(self.labels['Cnt'], 0, 0)
        rx_grid.addWidget(self.labels['Ref'], 0, 1)
        rx_grid.addWidget(self.labels['Act'], 0, 2)
        rx_grid.addWidget(self.labels['Phase'], 0, 3)
        rx_grid.addWidget(self.labels['Enc1'], 1, 0)
        rx_grid.addWidget(self.labels['Enc2'], 1, 1)
        rx_grid.addWidget(self.labels['Input'], 1, 2)
        rx_grid.addWidget(self.labels['Dist'], 1, 3)
        rx_grid.addWidget(self.labels['Linear'], 1, 4)
        layout.addLayout(rx_grid)
        
        # Capture controls
        capture_layout = QHBoxLayout()
        capture_layout.addWidget(self.other_widgets['file_name'])
        capture_layout.addStretch(1)
        capture_layout.addWidget(self.buttons['capture'])
        capture_layout.addWidget(self.buttons['stop'])
        capture_layout.addWidget(self.buttons['plot'])
        capture_layout.addWidget(self.buttons['save'])
        layout.addLayout(capture_layout)
        
        # Robot control, parameter, and controller settings
        h_layout = QHBoxLayout()
        
        # Robot control buttons
        grid = QGridLayout()
        grid.addWidget(self.buttons['inittorque'], 0, 0, 1, 2)
        grid.addWidget(self.buttons['roboton'], 1, 0)
        grid.addWidget(self.buttons['assiston'], 1, 1)
        grid.addWidget(self.buttons['robotoff'], 3, 0)
        grid.addWidget(self.buttons['assistoff'], 3, 1)
        h_layout.addLayout(grid)
        
        # Controller settings
        layout_ctrl = self.build_controller_layout()
        h_layout.addLayout(layout_ctrl)
        
        # Parameter settings
        layout_param, _ = self.build_parameter_layout()
        h_layout.addLayout(layout_param)
        
        layout.addLayout(h_layout)
        
        return layout

    def build_tab2_layout(self):
        """Tab 2 (System Identification) 레이아웃"""
        layout = QVBoxLayout()
        
        # Info box
        layout.addWidget(self.other_widgets['sysid_infoBox'])
        
        # Settings grid
        sysid_grid = QGridLayout()
        sysid_grid.addWidget(self.labels['sysid_freq_min'], 0, 0, 1, 2)
        sysid_grid.addWidget(self.labels['sysid_freq_max'], 0, 2, 1, 2)
        sysid_grid.addWidget(self.labels['sysid_n_sample'], 1, 0, 1, 2)
        sysid_grid.addWidget(self.labels['sysid_n_iter'], 1, 2, 1, 2)
        sysid_grid.addWidget(self.labels['sysid_mag'], 2, 0, 1, 2)
        sysid_grid.addWidget(self.labels['sysid_offset'], 2, 2, 1, 2)
        sysid_grid.addWidget(self.labels['sysid_file_name'], 3, 0, 1, 3)
        sysid_grid.addWidget(self.buttons['sysid_apply'], 3, 3, 1, 1)
        sysid_grid.addWidget(self.buttons['sysid_start'], 4, 1, 1, 1)
        sysid_grid.addWidget(self.buttons['sysid_stop'], 4, 2, 1, 1)
        sysid_grid.addWidget(self.buttons['sysid_save'], 4, 3, 1, 1)
        
        layout.addLayout(sysid_grid)
        
        return layout

    def build_main_window(self, gui_widget):
        """메인 윈도우 구성"""
        # Create all components first
        self.create_buttons()
        self.create_labels()
        self.create_checkboxes()
        self.create_title_labels()
        self.create_node_selection()
        
        # Create main layout
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        
        # Add node selection at top
        main_layout.addWidget(self.other_widgets['node_selection'])
        
        # Create tabs
        tabs = QTabWidget()
        tab1 = QWidget()
        tab2 = QWidget()
        
        # Set layouts
        tab1.setLayout(self.build_tab1_layout())
        tab2.setLayout(self.build_tab2_layout())
        
        # Add tabs
        tabs.addTab(tab1, "Human Walking Test")
        tabs.addTab(tab2, "System Identification")
        
        main_layout.addWidget(tabs)
        central_widget.setLayout(main_layout)
        
        gui_widget.setCentralWidget(central_widget)
        gui_widget.setWindowTitle('Flexi-SEA Control GUI')
        gui_widget.setGeometry(30, 100, 1200, 800)
        
        self.tabs['main'] = tabs
        self.tabs['tab1'] = tab1
        self.tabs['tab2'] = tab2
        
        return {
            'central_widget': central_widget,
            'buttons': self.buttons,
            'labels': self.labels,
            'checkboxes': self.checkboxes,
            'tabs': tabs,
            'parameter_inputs': self.labels,
            'other_widgets': self.other_widgets,
            'window_title': 'Flexi-SEA Control GUI'
        }
