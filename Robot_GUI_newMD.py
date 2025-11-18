#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Robot GUI - Main application entry point
Orchestrates UI, data management, parameter control, and robot communication
"""

import sys
import os
import glob
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QFileDialog
from PyQt5.QtCore import QTimer

# Import custom modules
from ui_builder import UIBuilder
from pcan_communicator import PCANCommunicator
from robot_controller import RobotController
from sysid_controller import SystemIDController
from data_manager import DataManager
from parameter_controller import ParameterController
from plot_graph import DataProcessor, DataVisualizer


class RobotGUI(QMainWindow):
    """Main GUI class - orchestrates all components"""
    
    def __init__(self):
        super().__init__()
        
        # Initialize PCAN communication
        self.pcan_comm = PCANCommunicator()
        
        # Current node ID selection (default to RIGHT/0x07)
        self.current_node_id = 0x07
        
        # Initialize controllers
        self.robot_ctrl = RobotController(self.pcan_comm, node_id=self.current_node_id)
        self.sysid_ctrl = SystemIDController(self.pcan_comm, node_id=self.current_node_id)
        self.data_mgr = DataManager(self.pcan_comm)
        self.param_ctrl = ParameterController(self.pcan_comm, node_id=self.current_node_id)
        
        # Initialize UI builder and build all components
        self.ui_builder = UIBuilder()
        self.components = self.ui_builder.build_main_window(self)
        
        # Set GUI reference for robot controller (for routine list building)
        self.robot_ctrl.set_gui_reference(self)
        
        # Set GUI reference for parameter controller
        self.param_ctrl.set_gui_reference(self)
        
        # Extract button references
        self.buttons_dict = self.components['buttons']
        self.labels_dict = self.components['labels']
        self.checkboxes_dict = self.components['checkboxes']
        self.other_widgets_dict = self.components.get('other_widgets', {})
        self.tabs = self.components['tabs']
        
        # Data for current session
        self.current_data = {}
        self.output_filename = ''
        self.sysid_data = {}
        self.sysid_output_filename = ''
        
        # Set central widget
        self.setCentralWidget(self.components['central_widget'])
        self.setWindowTitle(self.components['window_title'])
        self.setGeometry(30, 100, 1200, 800)
        
        # Connect all signals
        self._connect_signals()
        
        # Initialize timer for periodic updates
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_display)
        self.update_timer.start(100)
        
        # Auto-initialize PCAN on startup
        self.pcan_comm.initialize()
        
        self.show()
    
    def _connect_signals(self):
        """Connect all button signals to their handlers"""
        try:
            # Node selection
            if 'node_button_group' in self.other_widgets_dict:
                button_group = self.other_widgets_dict['node_button_group']
                button_group.buttonClicked.connect(self.on_node_selection_changed)
            
            # Robot control
            if 'roboton' in self.buttons_dict:
                self.buttons_dict['roboton'].clicked.connect(self.robot_on)
            if 'robotoff' in self.buttons_dict:
                self.buttons_dict['robotoff'].clicked.connect(self.robot_off)
            if 'assiston' in self.buttons_dict:
                self.buttons_dict['assiston'].clicked.connect(self.assist_on)
            if 'assistoff' in self.buttons_dict:
                self.buttons_dict['assistoff'].clicked.connect(self.assist_off)
            
            # Data management
            if 'capture' in self.buttons_dict:
                self.buttons_dict['capture'].clicked.connect(self.capture_data)
            if 'stop' in self.buttons_dict:
                self.buttons_dict['stop'].clicked.connect(self.stop_recording)
            if 'save' in self.buttons_dict:
                self.buttons_dict['save'].clicked.connect(self.save_data)
            if 'plot' in self.buttons_dict:
                self.buttons_dict['plot'].clicked.connect(self.plot_graph)
            
            # Parameter management
            if 'shiftleft' in self.buttons_dict:
                self.buttons_dict['shiftleft'].clicked.connect(self.shift_left)
            if 'shiftright' in self.buttons_dict:
                self.buttons_dict['shiftright'].clicked.connect(self.shift_right)
            if 'setCtrl' in self.buttons_dict:
                self.buttons_dict['setCtrl'].clicked.connect(self.set_ctrl)
            if 'setParam' in self.buttons_dict:
                self.buttons_dict['setParam'].clicked.connect(self.set_param)
            
            # Connection/Test
            if 'connect' in self.buttons_dict:
                self.buttons_dict['connect'].clicked.connect(self.connect_pcan)
            if 'inittorque' in self.buttons_dict:
                self.buttons_dict['inittorque'].clicked.connect(self.init_torque)
                
        except Exception as e:
            print(f"Signal connection error: {e}")
    
    # ===================== Robot Control Methods =====================
    
    def robot_on(self):
        """Turn on robot"""
        try:
            # PCAN 초기화 확인
            if not self.pcan_comm.obj_pcan_basic:
                self.show_error("Error", "PCAN not initialized. Please connect first.")
                return
            
            self.robot_ctrl.robot_on()
            # Update button states
            if 'roboton' in self.buttons_dict:
                self.buttons_dict['roboton'].setChecked(True)
            if 'robotoff' in self.buttons_dict:
                self.buttons_dict['robotoff'].setChecked(False)
            self.show_info("Success", "Robot turned ON")
        except Exception as e:
            self.show_error("Error", f"Robot on failed: {str(e)}")
    
    def robot_off(self):
        """Turn off robot"""
        try:
            if not self.pcan_comm.obj_pcan_basic:
                self.show_error("Error", "PCAN not initialized. Please connect first.")
                return
            
            self.robot_ctrl.robot_off()
            # Update button states
            if 'roboton' in self.buttons_dict:
                self.buttons_dict['roboton'].setChecked(False)
            if 'robotoff' in self.buttons_dict:
                self.buttons_dict['robotoff'].setChecked(True)
            self.show_info("Info", "Robot turned OFF")
        except Exception as e:
            self.show_error("Error", f"Robot off failed: {str(e)}")
    
    def assist_on(self):
        """Turn on assist mode"""
        try:
            if not self.pcan_comm.obj_pcan_basic:
                self.show_error("Error", "PCAN not initialized. Please connect first.")
                return
            
            self.robot_ctrl.assist_on()
            # Update button states
            if 'assiston' in self.buttons_dict:
                self.buttons_dict['assiston'].setChecked(True)
            if 'assistoff' in self.buttons_dict:
                self.buttons_dict['assistoff'].setChecked(False)
            self.show_info("Success", "Assist mode ON")
        except Exception as e:
            self.show_error("Error", f"Assist on failed: {str(e)}")
    
    def assist_off(self):
        """Turn off assist mode"""
        try:
            if not self.pcan_comm.obj_pcan_basic:
                self.show_error("Error", "PCAN not initialized. Please connect first.")
                return
            
            self.robot_ctrl.assist_off()
            # Update button states
            if 'assiston' in self.buttons_dict:
                self.buttons_dict['assiston'].setChecked(False)
            if 'assistoff' in self.buttons_dict:
                self.buttons_dict['assistoff'].setChecked(True)
            self.show_info("Info", "Assist mode OFF")
        except Exception as e:
            self.show_error("Error", f"Assist off failed: {str(e)}")
    
    def test_robot(self):
        """Test robot communication"""
        try:
            if not self.pcan_comm.obj_pcan_basic:
                self.show_error("Error", "PCAN not initialized. Please connect first.")
                return
            
            self.robot_ctrl.test()
            self.show_info("Info", "Robot test completed")
        except Exception as e:
            self.show_error("Error", f"Robot test failed: {str(e)}")
    
    def init_torque(self):
        """Initialize torque"""
        try:
            if not self.pcan_comm.obj_pcan_basic:
                self.show_error("Error", "PCAN not initialized. Please connect first.")
                return
            
            self.robot_ctrl.init_torque()
            self.show_info("Success", "Torque initialized")
        except Exception as e:
            self.show_error("Error", f"Init torque failed: {str(e)}")
    
    # ===================== Data Management Methods =====================
    
    def capture_data(self):
        """Start data capture/trace"""
        try:
            if not self.pcan_comm.obj_pcan_basic:
                self.show_error("Error", "PCAN not initialized. Please connect first.")
                return
            
            self.data_mgr.configure_and_start_trace()
            self.show_info("Success", "Data recording started")
        except Exception as e:
            self.show_error("Error", f"Data capture failed: {str(e)}")
    
    def stop_recording(self):
        """Stop data recording"""
        try:
            self.data_mgr.stop_trace()
            self.show_info("Info", "Data recording stopped")
        except Exception as e:
            self.show_error("Error", f"Stop recording failed: {str(e)}")
    
    def save_data(self):
        """Save recorded data to text file"""
        try:
            if not self.current_data or not any(len(v) > 0 for v in self.current_data.values()):
                self.show_warning("Warning", "No data to save")
                return
            
            # 자동 파일명 생성 또는 기존 파일명 사용
            if not self.output_filename:
                self.output_filename = self.generate_output_filename("data")
            
            filename = self.data_mgr.save_to_txt_with_data(self.current_data, self.output_filename)
            self.show_info("Success", f"Data saved to {filename}")
        except Exception as e:
            self.show_error("Error", f"Save failed: {str(e)}")
    
    def plot_graph(self):
        """Plot loaded data or select file to plot"""
        try:
            # 파일 선택 다이얼로그
            options = QFileDialog.Options()
            filename, _ = QFileDialog.getOpenFileName(
                self, "Select TRC File", "", 
                "TRC Files (*.trc);;All Files (*)", 
                options=options)
            
            if filename:
                # 선택한 파일 처리 및 시각화 창 열기
                processor = DataProcessor(filename, node_id=self.current_node_id)
                processor.load_data()
                self.show_plot_window(processor.data)
                self.output_filename = self.generate_output_filename(filename)
                self.current_data = processor.data
                self.show_info("Success", "Plot displayed")
        except Exception as e:
            self.show_error("Error", f"Plot failed: {str(e)}")
    
    def show_plot_window(self, data):
        """Show data visualization in a new window"""
        try:
            self.plot_window = DataVisualizer(data)
            self.plot_window.show()
        except Exception as e:
            self.show_error("Error", f"Plot window failed: {str(e)}")
    
    # ===================== Parameter Control Methods =====================
    
    def set_ctrl(self):
        """Set control parameters"""
        try:
            if not self.pcan_comm.obj_pcan_basic:
                self.show_error("Error", "PCAN not initialized. Please connect first.")
                return
            
            # Get parameters from UI
            params = self._get_input_params()
            self.param_ctrl.set_control_parameters(**params)
            self.show_info("Success", "Control parameters updated")
        except Exception as e:
            self.show_error("Error", f"Set control failed: {str(e)}")
    
    def set_param(self):
        """Set parameters based on current parameter tab"""
        try:
            if not self.pcan_comm.obj_pcan_basic:
                self.show_error("Error", "PCAN not initialized. Please connect first.")
                return
            
            params = self._get_input_params()
            # Get current tab index from parameter tabs (not main tabs)
            param_tab_index = self.ui_builder.tabs['ref'].currentIndex()
            
            if param_tab_index == 0:  # Walking
                self.param_ctrl.set_walking_parameters(**params)
            elif param_tab_index == 1:  # Sine
                self.param_ctrl.set_sine_parameters(
                    amp=params.get('refsine_amp', 0),
                    freq=params.get('refsine_freq', 0)
                )
            elif param_tab_index == 2:  # Square (Tanh)
                self.param_ctrl.set_square_parameters(
                    amp=params.get('reftanh_amp', 0),
                    a=params.get('reftanh_a', 0),
                    td=params.get('reftanh_td', 0)
                )
            elif param_tab_index == 3:  # Ankle (Periodic)
                self.param_ctrl.set_periodic_ankle_parameters(
                    plantar_amp=params.get('refAnkle_amp', 0),
                    peak=params.get('refAnkle_peak', 0),
                    ratio=params.get('refAnkle_ratio', 0),
                    width=params.get('refAnkle_width', 0)
                )
            elif param_tab_index == 4:  # SAAN
                self.param_ctrl.set_saan_parameters(
                    k_torque=params.get('saan_k_torque', 0),
                    max_torque=params.get('saan_max_torque', 0),
                    power_PF=params.get('saan_power_PF', 1),
                    power_DF=params.get('saan_power_DF', 1)
                )
            
            self.show_info("Success", "Parameters applied")
        except Exception as e:
            self.show_error("Error", f"Set param failed: {str(e)}")
    
    def shift_left(self):
        """Shift parameters left"""
        try:
            if not self.pcan_comm.obj_pcan_basic:
                self.show_error("Error", "PCAN not initialized. Please connect first.")
                return
            
            self.param_ctrl.shift_parameters_left()
            self.show_info("Info", "Parameters shifted left")
        except Exception as e:
            self.show_error("Error", f"Shift left failed: {str(e)}")
    
    def shift_right(self):
        """Shift parameters right"""
        try:
            if not self.pcan_comm.obj_pcan_basic:
                self.show_error("Error", "PCAN not initialized. Please connect first.")
                return
            
            self.param_ctrl.shift_parameters_right()
            self.show_info("Info", "Parameters shifted right")
        except Exception as e:
            self.show_error("Error", f"Shift right failed: {str(e)}")
    
    # ===================== PCAN Communication =====================
    
    def connect_pcan(self):
        """Connect to PCAN"""
        try:
            if self.pcan_comm.initialize():
                self.show_info("Success", "PCAN connected successfully")
            else:
                self.show_error("Error", "Failed to connect to PCAN")
        except Exception as e:
            self.show_error("Error", f"Connection error: {str(e)}")
    
    # ===================== Helper Methods =====================
    
    def _get_input_params(self):
        """Extract input parameters from UI labels"""
        params = {}
        for key, widget in self.labels_dict.items():
            try:
                # LabeledLineEdit 위젯의 lineEdit 속성에서 값 추출
                if hasattr(widget, 'lineEdit'):
                    value = widget.lineEdit.text()
                    if value:
                        try:
                            params[key] = float(value)
                        except:
                            params[key] = value
            except:
                pass
        return params
    
    def generate_output_filename(self, base_name):
        """Generate output filename with parameters and checkbox states"""
        # Extract base filename
        output_filename = os.path.splitext(os.path.basename(base_name))[0]
        if output_filename.endswith("_metadata"):
            output_filename = output_filename[:-9]  # Remove _metadata suffix
        
        # Add checkbox states
        if self.checkboxes_dict.get('PD') and self.checkboxes_dict['PD'].isChecked():
            output_filename += '_PD'
        if self.checkboxes_dict.get('FF') and self.checkboxes_dict['FF'].isChecked():
            output_filename += '_FF'
        if self.checkboxes_dict.get('DOB') and self.checkboxes_dict['DOB'].isChecked():
            output_filename += '_DOB'
        if self.checkboxes_dict.get('LS') and self.checkboxes_dict['LS'].isChecked():
            output_filename += '_LS'
        if self.checkboxes_dict.get('Fric') and self.checkboxes_dict['Fric'].isChecked():
            output_filename += '_Fric'
        
        # Add key parameters
        try:
            kp_text = self.labels_dict.get('Kp').lineEdit.text() if 'Kp' in self.labels_dict else '0.2'
            kd_text = self.labels_dict.get('Kd').lineEdit.text() if 'Kd' in self.labels_dict else '0.0001'
            t_plantar_text = self.labels_dict.get('Plantar').lineEdit.text() if 'Plantar' in self.labels_dict else '5'
            t1_text = self.labels_dict.get('T1').lineEdit.text() if 'T1' in self.labels_dict else '55'
            t2_text = self.labels_dict.get('T2').lineEdit.text() if 'T2' in self.labels_dict else '0.714'
            t3_text = self.labels_dict.get('T3').lineEdit.text() if 'T3' in self.labels_dict else '60'
            
            output_filename += f'_Kp{kp_text}_Kd{kd_text}_T{t_plantar_text}_P{t1_text}_R{t2_text}_W{t3_text}'
        except:
            pass
        
        return output_filename + '.txt'
    
    def load_latest_trc_file(self):
        """Load and plot latest .trc file"""
        try:
            folder_path = "./"
            list_of_files = glob.glob(os.path.join(folder_path, "*.trc"))
            
            if not list_of_files:
                self.show_warning("Warning", "No .trc files found")
                return
            
            filename = max(list_of_files, key=os.path.getmtime)
            processor = DataProcessor(filename, node_id=self.current_node_id)
            processor.load_data()
            self.show_plot_window(processor.data)
            self.output_filename = self.generate_output_filename(filename)
            self.current_data = processor.data
            self.show_info("Success", f"Loaded latest file: {os.path.basename(filename)}")
        except Exception as e:
            self.show_error("Error", f"Load file failed: {str(e)}")
    
    def load_sysid_latest_file(self):
        """Load and display latest SysID file"""
        try:
            folder_path = "./"
            list_of_files = glob.glob(os.path.join(folder_path, "*sysid*.txt"))
            
            if not list_of_files:
                self.show_warning("Warning", "No SysID files found")
                return
            
            filename = max(list_of_files, key=os.path.getmtime)
            self.sysid_output_filename = filename
            self.show_info("Success", f"Loaded SysID file: {os.path.basename(filename)}")
        except Exception as e:
            self.show_error("Error", f"Load SysID file failed: {str(e)}")
    
    def _update_display(self):
        """Periodic update of display elements"""
        try:
            if self.pcan_comm:
                messages = self.pcan_comm.read_all_messages()
        except:
            pass
    
    def on_node_selection_changed(self, button):
        """Handle node selection change"""
        try:
            # Get selected node ID from button group
            if 'node_button_group' in self.other_widgets_dict:
                button_group = self.other_widgets_dict['node_button_group']
                self.current_node_id = button_group.checkedId()
                
                # Update all controllers with new node ID
                self.robot_ctrl.node_id = self.current_node_id
                self.sysid_ctrl.node_id = self.current_node_id
                self.param_ctrl.node_id = self.current_node_id
                
                node_name = "LEFT (0x06)" if self.current_node_id == 0x06 else "RIGHT (0x07)"
                self.show_info("Info", f"Switched to {node_name}")
                print(f"Node ID changed to: 0x{self.current_node_id:02X}")
        except Exception as e:
            print(f"Node selection error: {e}")
    
    def show_info(self, title, message):
        """Show info message box"""
        QMessageBox.information(self, title, message)
    
    def show_error(self, title, message):
        """Show error message box"""
        QMessageBox.critical(self, title, message)
    
    def show_warning(self, title, message):
        """Show warning message box"""
        QMessageBox.warning(self, title, message)
    
    def closeEvent(self, event):
        """Handle window close event"""
        try:
            self.update_timer.stop()
            if self.pcan_comm:
                self.pcan_comm.close()
            event.accept()
        except:
            event.accept()


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    gui = RobotGUI()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
