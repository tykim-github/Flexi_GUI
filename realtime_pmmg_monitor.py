"""
Real-time pMMG Monitor - Displays muscle sensor data in real-time
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog, 
                             QMessageBox, QGridLayout, QLineEdit, QGroupBox, QScrollArea)
from PyQt5.QtCore import QTimer, pyqtSignal, QObject
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
from collections import deque
from datetime import datetime
import os
from calibration_processor import CalibrationProcessor


class RealtimePMMGMonitor(QWidget):
    """Real-time pMMG data monitoring widget"""
    
    # Signal to notify parent when start/stop is clicked
    start_requested = pyqtSignal()
    stop_requested = pyqtSignal()
    send_calib_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Display buffers (rolling window for graph - maxlen 제한)
        self.buffer_size = 2000  # 10 seconds at 50Hz
        self.display_window = 10000  # cnt 범위 (대략 5000ms = 5초 분량)
        self.cnt_buffer = deque(maxlen=self.buffer_size)
        self.pmmg1_buffer = deque(maxlen=self.buffer_size)
        self.pmmg2_buffer = deque(maxlen=self.buffer_size)
        self.ankle_angle_buffer = deque(maxlen=self.buffer_size)
        self.gamma_buffer = deque(maxlen=self.buffer_size)
        
        # Recording buffers (START부터 STOP까지 모든 데이터 저장 - 제한 없음)
        self.cnt_recording = []
        self.pmmg1_recording = []
        self.pmmg2_recording = []
        self.ankle_angle_recording = []
        self.gamma_recording = []
        
        # Calibration parameters (16개)
        self.calib_params = [0.0] * 16
        self.calib_param_inputs = []
        
        self.sample_counter = 0  # Counter for 50Hz subsampling (every 20 samples)
        self.skip_count = 0  # Counter to skip first 400 samples
        self.monitoring = False
        
        # Calibration processor
        self.calib_processor = CalibrationProcessor(fs=60)
        
        # Setup UI
        self._setup_ui()
        
        # Timer for graph updates (50Hz = 20ms)
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_graph)
        self.update_interval = 20  # ms
        
    def _setup_ui(self):
        """Setup UI layout"""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Real-time pMMG Monitor")
        title_font = title.font()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Graph (reduced height)
        self.figure = Figure(figsize=(12, 10), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setMaximumHeight(550)  # Limit graph height
        self.ax1 = self.figure.add_subplot(311)
        self.ax2 = self.figure.add_subplot(312)
        self.ax3 = self.figure.add_subplot(313)
        self.figure.subplots_adjust(left=0.1, right=0.95, top=0.95, bottom=0.1, hspace=0.4)
        layout.addWidget(self.canvas)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("START Monitor")
        self.start_btn.setStyleSheet("background-color: green; color: white; font-size: 12pt; font-weight: bold;")
        self.start_btn.setFixedHeight(50)
        self.start_btn.clicked.connect(self._on_start_clicked)
        button_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("STOP Monitor")
        self.stop_btn.setStyleSheet("background-color: red; color: white; font-size: 12pt; font-weight: bold;")
        self.stop_btn.setFixedHeight(50)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._on_stop_clicked)
        button_layout.addWidget(self.stop_btn)
        
        self.save_btn = QPushButton("SAVE Data")
        self.save_btn.setStyleSheet("background-color: blue; color: white; font-size: 12pt; font-weight: bold;")
        self.save_btn.setFixedHeight(50)
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self._on_save_clicked)
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)
        
        # Calibration button section
        calib_button_layout = QHBoxLayout()
        
        self.load_calib_btn = QPushButton("Load Calib File")
        self.load_calib_btn.setStyleSheet("background-color: purple; color: white; font-size: 12pt; font-weight: bold;")
        self.load_calib_btn.setFixedHeight(50)
        self.load_calib_btn.clicked.connect(self._on_load_calib_clicked)
        calib_button_layout.addWidget(self.load_calib_btn)
        
        layout.addLayout(calib_button_layout)
        
        # Info label
        self.info_label = QLabel("Status: Idle | Samples: 0")
        layout.addWidget(self.info_label)
        
        # Calibration Parameters Section
        calib_group = QGroupBox("Calibration Parameters (16 values)")
        calib_layout = QGridLayout()
        
        param_labels = [
            'a_rest_DF', 'b_rest_DF', 'c_rest_DF', 'd_rest_DF',
            'a_cont_DF', 'b_cont_DF', 'c_cont_DF', 'd_cont_DF',
            'a_rest_PF', 'b_rest_PF', 'c_rest_PF', 'd_rest_PF',
            'a_cont_PF', 'b_cont_PF', 'c_cont_PF', 'd_cont_PF'
        ]
        
        # Default calibration values
        default_values = [
            104.50637491, -0.00201688, 7.48004137, 0.02000000,  # rest_DF
            6.48577335, 50.58618430, 45.12870713, 112.85984928,  # cont_DF
            104.29520766, -0.00224707, 6.62748709, 0.02000000,  # rest_PF
            1.86059261, 25.84767487, 9.57775943, 115.61136262   # cont_PF
        ]
        
        for i, label_text in enumerate(param_labels):
            row = i // 4
            col = i % 4
            
            label = QLabel(label_text)
            label_font = label.font()
            label_font.setPointSize(10)
            label_font.setBold(True)
            label.setFont(label_font)
            
            line_edit = QLineEdit(f"{default_values[i]:.8f}")
            line_edit.setMinimumWidth(120)
            line_edit.setMaximumWidth(150)
            
            # Set font for better readability
            edit_font = line_edit.font()
            edit_font.setPointSize(10)
            edit_font.setFamily("Courier New")  # Monospace font for numbers
            line_edit.setFont(edit_font)
            
            self.calib_param_inputs.append(line_edit)
            
            calib_layout.addWidget(label, row, col * 2)
            calib_layout.addWidget(line_edit, row, col * 2 + 1)
        
        calib_group.setLayout(calib_layout)
        
        # Send calibration button
        self.send_calib_btn = QPushButton("Send Calibration Params")
        self.send_calib_btn.setStyleSheet("background-color: orange; color: white; font-size: 10pt; font-weight: bold;")
        self.send_calib_btn.setFixedHeight(40)
        self.send_calib_btn.clicked.connect(self._on_send_calib_clicked)
        
        # Add calibration section directly (no scroll)
        layout.addWidget(calib_group)
        layout.addWidget(self.send_calib_btn)
        
        self.setLayout(layout)
    
    def _on_start_clicked(self):
        """Handle start button click"""
        self.start_requested.emit()
    
    def _on_stop_clicked(self):
        """Handle stop button click"""
        self.stop_requested.emit()
    
    def _on_send_calib_clicked(self):
        """Handle send calibration params button click"""
        try:
            # 모든 입력값을 읽기
            params = []
            for i, input_field in enumerate(self.calib_param_inputs):
                value = float(input_field.text())
                params.append(value)
            
            if len(params) != 16:
                QMessageBox.warning(self, "Error", f"Expected 16 parameters, got {len(params)}")
                return
            
            # Signal 발송 (Robot_GUI_newMD에서 수신)
            self.send_calib_requested.emit()
            
            QMessageBox.information(self, "Success", 
                                  "Calibration parameters sent to robot!")
        except ValueError as e:
            QMessageBox.warning(self, "Error", 
                              f"Invalid parameter value: {str(e)}")
    
    def get_calibration_params(self):
        """입력된 16개 calibration parameter 반환"""
        try:
            params = []
            for input_field in self.calib_param_inputs:
                value = float(input_field.text())
                params.append(value)
            return params
        except ValueError:
            return None
    
    def _on_load_calib_clicked(self):
        """Handle load calibration file button click"""
        try:
            # File dialog to select calibration data file
            filename, _ = QFileDialog.getOpenFileName(
                self,
                "Select Calibration Data File",
                "",
                "Text Files (*.txt);;All Files (*)"
            )
            
            if not filename:
                return
            
            # Process calibration data
            if not self.calib_processor.load_and_process(filename):
                QMessageBox.critical(self, "Error", "Failed to process calibration file")
                return
            
            # Show time series plot (external window)
            self.calib_processor.plot_time_series(filename)
            
            # Show fitting results plot (external window)
            self.calib_processor.plot_fitting_results()
            
            # Get coefficients and populate input fields
            coeffs = self.calib_processor.get_coefficients_list()
            
            if len(coeffs) != 16:
                QMessageBox.critical(self, "Error", 
                                   f"Expected 16 coefficients, got {len(coeffs)}")
                return
            
            # Fill in the input fields
            for i, coeff in enumerate(coeffs):
                self.calib_param_inputs[i].setText(f"{coeff:.8f}")
            
            # Show success message
            QMessageBox.information(self, "Success", 
                                  "Calibration coefficients loaded successfully!\n"
                                  "Two plot windows have been opened for verification.")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load calibration: {str(e)}")
    
    def is_monitoring(self):
        """Check if currently monitoring"""
        return self.monitoring
    
    def start_monitoring(self):
        """Start real-time monitoring"""
        self.monitoring = True
        self.sample_counter = 0
        self.skip_count = 0  # Reset skip counter
        # Clear display buffers (rolling window)
        self.cnt_buffer.clear()
        self.pmmg1_buffer.clear()
        self.pmmg2_buffer.clear()
        self.ankle_angle_buffer.clear()
        self.gamma_buffer.clear()
        # Clear recording buffers for new session
        self.cnt_recording = []
        self.pmmg1_recording = []
        self.pmmg2_recording = []
        self.ankle_angle_recording = []
        self.gamma_recording = []
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.save_btn.setEnabled(False)
        self.info_label.setText("Status: Monitoring...")
        self.update_timer.start(self.update_interval)
    
    def stop_monitoring(self):
        """Stop real-time monitoring"""
        self.update_timer.stop()
        self.monitoring = False
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.save_btn.setEnabled(True)
        self.info_label.setText(f"Status: Stopped - {len(self.cnt_buffer)} samples collected")
    
    def _on_save_clicked(self):
        """Handle save button click - save data to file"""
        if len(self.cnt_buffer) == 0:
            QMessageBox.warning(self, "Warning", "No data to save!")
            return
        
        # File dialog to select save location
        filename, _ = QFileDialog.getSaveFileName(
            self, 
            "Save pMMG Data", 
            "",
            "Text Files (*.txt);;CSV Files (*.csv)"
        )
        
        if filename:
            try:
                self._save_data_to_file(filename)
                QMessageBox.information(self, "Success", f"Data saved to {filename}")
                self.save_btn.setEnabled(False)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save file: {str(e)}")
    
    def _save_data_to_file(self, filename):
        """Save collected data to file (5 columns)"""
        # Use recording buffers (START~STOP 모든 데이터)
        with open(filename, 'w') as f:
            # Write header
            f.write("cnt\tpMMG1\tpMMG2\tAnkle_Angle\tGamma\n")
            
            # Write data
            for cnt, pmmg1, pmmg2, ankle_angle, gamma in zip(self.cnt_recording, self.pmmg1_recording, 
                                                                self.pmmg2_recording, self.ankle_angle_recording,
                                                                self.gamma_recording):
                f.write(f"{cnt}\t{pmmg1:.6f}\t{pmmg2:.6f}\t{ankle_angle:.6f}\t{gamma:.6f}\n")
    
    def clear_data(self):
        """Clear all data buffers"""
        self.cnt_buffer.clear()
        self.pmmg1_buffer.clear()
        self.pmmg2_buffer.clear()
        self.ankle_angle_buffer.clear()
        self.gamma_buffer.clear()
        self.sample_counter = 0
        self.info_label.setText("Status: Data cleared")
        self._update_graph()
    
    def add_data(self, cnt, pmmg1, pmmg2, ankle_angle, gamma=0.0):
        """
        Add new data point (called at 1kHz from data receiver)
        
        Parameters:
            cnt: Counter value (uint32, received as float) - in milliseconds
            pmmg1: First pMMG value
            pmmg2: Second pMMG value
            ankle_angle: Ankle angle from absolute encoder (degrees)
            gamma: CCI (co-contraction index) value
        """
        if self.monitoring:
            # Subsample to 50Hz (every 20 samples)
            self.sample_counter += 1
            if self.sample_counter >= 20:
                self.sample_counter = 0
                
                # Skip first 400 samples
                self.skip_count += 1
                if self.skip_count <= 400:
                    return  # Skip this sample
                
                # Store original cnt value directly (no time conversion)
                cnt_int = int(cnt)
                
                # Add to display buffer (rolling window)
                self.cnt_buffer.append(cnt_int)
                self.pmmg1_buffer.append(pmmg1)
                self.pmmg2_buffer.append(pmmg2)
                self.ankle_angle_buffer.append(ankle_angle)
                self.gamma_buffer.append(gamma)
                
                # Add to recording buffer (START~STOP 모든 데이터)
                self.cnt_recording.append(cnt_int)
                self.pmmg1_recording.append(pmmg1)
                self.pmmg2_recording.append(pmmg2)
                self.ankle_angle_recording.append(ankle_angle)
                self.gamma_recording.append(gamma)
                
                # Update info label
                self.info_label.setText(f"Status: Monitoring | Samples: {len(self.cnt_recording)} | Last cnt: {cnt_int}")
    
    def _update_graph(self):
        """Update graph display (3 subplots)"""
        self.ax1.clear()
        self.ax2.clear()
        self.ax3.clear()
        
        if len(self.cnt_buffer) > 0:
            cnt_list = list(self.cnt_buffer)
            pmmg1_list = list(self.pmmg1_buffer)
            pmmg2_list = list(self.pmmg2_buffer)
            ankle_angle_list = list(self.ankle_angle_buffer)
            gamma_list = list(self.gamma_buffer)
            
            # Convert cnt (ms) to time (sec)
            time_list = [c / 1000.0 for c in cnt_list]
            
            # Plot pMMG data (top subplot)
            self.ax1.plot(time_list, pmmg1_list, 'b-', label='pMMG1', linewidth=2)
            self.ax1.plot(time_list, pmmg2_list, 'r-', label='pMMG2', linewidth=2)
            
            # Plot Ankle Angle data (middle subplot)
            self.ax2.plot(time_list, ankle_angle_list, 'g-', label='Ankle Angle', linewidth=2)
            
            # Plot Gamma data (bottom subplot)
            self.ax3.plot(time_list, gamma_list, 'm-', label='Gamma (CCI)', linewidth=2)
            
            # Set x-axis limit to show rolling window (last 10 seconds)
            time_last = time_list[-1]
            if time_last > self.display_window / 1000.0:
                xlim_start = time_last - self.display_window / 1000.0
                xlim_end = time_last
            else:
                xlim_start = 0
                xlim_end = self.display_window / 1000.0
            
            # Configure pMMG plot
            self.ax1.set_xlim(xlim_start, xlim_end)
            self.ax1.set_xlabel('Time (sec)')
            self.ax1.set_ylabel('pMMG Value')
            self.ax1.legend(loc='upper right')
            self.ax1.grid(True, alpha=0.3)
            
            # Configure Ankle Angle plot
            self.ax2.set_xlim(xlim_start, xlim_end)
            self.ax2.set_xlabel('Time (sec)')
            self.ax2.set_ylabel('Angle (deg)')
            self.ax2.legend(loc='upper right')
            self.ax2.grid(True, alpha=0.3)
            
            # Configure Gamma plot
            self.ax3.set_xlim(xlim_start, xlim_end)
            self.ax3.set_xlabel('Time (sec)')
            self.ax3.set_ylabel('Gamma (CCI)')
            self.ax3.legend(loc='upper right')
            self.ax3.grid(True, alpha=0.3)
        else:
            self.ax1.text(0.5, 0.5, 'No data yet\nClick START Monitor to begin', 
                        horizontalalignment='center',
                        verticalalignment='center',
                        transform=self.ax1.transAxes,
                        fontsize=12)
            self.ax1.set_xlim(0, self.display_window / 1000.0)
            self.ax1.set_ylim(0, 1)
            self.ax1.set_xlabel('Time (sec)')
            self.ax1.set_ylabel('pMMG Value')
            self.ax1.grid(True, alpha=0.3)
            
            self.ax2.text(0.5, 0.5, 'No data yet', 
                        horizontalalignment='center',
                        verticalalignment='center',
                        transform=self.ax2.transAxes,
                        fontsize=12)
            self.ax2.set_xlim(0, self.display_window / 1000.0)
            self.ax2.set_ylim(-30, 30)
            self.ax2.set_xlabel('Time (sec)')
            self.ax2.set_ylabel('Angle (deg)')
            self.ax2.grid(True, alpha=0.3)
            
            self.ax3.text(0.5, 0.5, 'No data yet', 
                        horizontalalignment='center',
                        verticalalignment='center',
                        transform=self.ax3.transAxes,
                        fontsize=12)
            self.ax3.set_xlim(0, self.display_window / 1000.0)
            self.ax3.set_ylim(0, 1)
            self.ax3.set_xlabel('Time (sec)')
            self.ax3.set_ylabel('Gamma (CCI)')
            self.ax3.grid(True, alpha=0.3)
        
        self.canvas.draw()
