import sys
import os
import glob
import struct
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QFileDialog
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT
import matplotlib.pyplot as plt

class DataProcessor:
    def __init__(self, filename, node_id=0x07):
        self.filename = filename
        self.node_id = node_id
        # Convert node_id to data pattern (0x06 -> 0361, 0x07 -> 0371)
        self.data_pattern = '0361' if node_id == 0x06 else '0371'
        self.data = {'cnt': [], 'ref_force': [], 'torque': [], 'gait_phase': [], 
                     'enc1': [], 'enc2': [], 'dist': [], 'cur': [], 'FB': [], 'FF': [], 'gait_phase_widm': [], 'gait_period': [],
                     'freq':[],'mot_vel':[], 'force':[], 'done':[],'ref_vel':[],'pmmg1':[],'pmmg2':[],'gamma':[]}
    
    def load_data(self):
        with open(self.filename, 'r') as file:
            lines = file.readlines()[34:]  # Skip header lines
            frame_count = 0
            valid_frames = 0
            invalid_frames = 0
            wrong_id_frames = 0
            
            for line in lines:
                try:
                    # TRC 형식: "... CAN_ID Rx/Tx DLC data..."
                    # "Rx" 또는 "Tx" 위치 찾기
                    if 'Rx' not in line and 'Tx' not in line:
                        continue
                    
                    # Rx/Tx 이전 부분에서 CAN ID 추출
                    rx_tx_pos = line.find('Rx') if 'Rx' in line else line.find('Tx')
                    
                    # Rx/Tx 이전의 공백으로 구분된 토큰들
                    before_rx = line[:rx_tx_pos].strip().split()
                    
                    # 마지막 토큰이 CAN ID (16진수 형식)
                    if len(before_rx) < 1:
                        wrong_id_frames += 1
                        frame_count += 1
                        continue
                    
                    can_id = before_rx[-1]  # 마지막 토큰
                    
                    # CAN ID 검증 (0x0361 or 0x0371)
                    expected_id = '0361' if self.node_id == 0x06 else '0371'
                    if can_id != expected_id:
                        wrong_id_frames += 1
                        frame_count += 1
                        continue
                    
                    # hex 데이터 추출 (Rx/Tx 이후의 모든 hex 값)
                    rx_tx_marker = 'Rx' if 'Rx' in line else 'Tx'
                    index = line.index(rx_tx_marker) + len(rx_tx_marker)
                    hex_data = line[index:].split()  # DLC 포함, 이후부터 모두 추출
                    
                    # DLC 제거 (첫 번째 값이 DLC)
                    if len(hex_data) > 0:
                        hex_data = hex_data[1:]  # DLC 제거
                    
                    hex_str = ''.join(hex_data)
                    
                    # hex 데이터를 byte로 변환
                    recv_buffer = bytes.fromhex(hex_str)
                    
                    # 최소 길이 확인 (데이터가 충분해야 함)
                    if len(recv_buffer) < 61:
                        invalid_frames += 1
                        frame_count += 1
                        continue
                    
                    # 데이터 변환 - 오프셋에 따른 정확한 데이터 추출
                    cnt = struct.unpack('<i', recv_buffer[3:7])[0]
                    
                    # cnt 값의 이상 여부 확인
                    if cnt > 100000 or cnt < 0:
                        print(f"[SKIP] Frame {frame_count}: Invalid cnt={cnt}")
                        invalid_frames += 1
                        frame_count += 1
                        continue
                    
                    ref_force = struct.unpack('<f', recv_buffer[9:13])[0]
                    force = struct.unpack('<f', recv_buffer[15:19])[0]
                    enc1 = struct.unpack('<f', recv_buffer[21:25])[0]
                    cur = struct.unpack('<f', recv_buffer[27:31])[0]
                    ref_vel = struct.unpack('<f', recv_buffer[33:37])[0]
                    torque = struct.unpack('<f', recv_buffer[39:43])[0]
                    pmmg1 = struct.unpack('<f', recv_buffer[45:49])[0]
                    pmmg2 = struct.unpack('<f', recv_buffer[51:55])[0]
                    gamma = struct.unpack('<f', recv_buffer[57:61])[0]  # 실제로는 gamma
                    
                    # mot_vel 읽기 (65바이트 이상일 때만)
                    mot_vel = 0.0
                    if len(recv_buffer) >= 65:
                        mot_vel = struct.unpack('<f', recv_buffer[61:65])[0]  # 실제로는 mot_vel

                    # 데이터 저장
                    self.data['cnt'].append(cnt)
                    self.data['ref_force'].append(ref_force)
                    self.data['force'].append(force)
                    self.data['enc1'].append(enc1)
                    self.data['cur'].append(cur)
                    self.data['ref_vel'].append(ref_vel)
                    self.data['mot_vel'].append(mot_vel)
                    self.data['torque'].append(torque)
                    self.data['pmmg1'].append(pmmg1)
                    self.data['pmmg2'].append(pmmg2)
                    self.data['gamma'].append(gamma)
                    
                    valid_frames += 1
                    
                except (ValueError, struct.error, IndexError) as e:
                    invalid_frames += 1
                
                frame_count += 1
            
            print(f"\n[SUMMARY] Total frames: {frame_count}")
            print(f"  Valid (correct ID): {valid_frames}")
            print(f"  Wrong CAN ID: {wrong_id_frames}")
            print(f"  Invalid/Unpacking error: {invalid_frames}")

    def sysid_load_data(self):
        with open(self.filename, 'r') as file:
            lines = file.readlines()[34:]  # Skip header lines
            # cnt_pre=0
            for line in lines:
                if 'Rx' in line and self.data_pattern in line:
                    try:
                        # 'Rx' 위치를 찾고 데이터를 추출
                        index = line.index('Rx') + 5
                        hex_data = line[index:].split()  # Index 이후부터 데이터 추출
                        
                        # 한 줄의 데이터를 합쳐서 hex로 변환
                        hex_str = ''.join(hex_data)
                        
                        # hex 데이터를 byte로 변환
                        recv_buffer = bytes.fromhex(hex_str)
                        # 데이터 변환 - 오프셋에 따른 정확한 데이터 추출
                        vel = struct.unpack('<f', recv_buffer[3:7])[0]
                        freq = struct.unpack('<f', recv_buffer[9:13])[0]
                        current = struct.unpack('<f', recv_buffer[15:19])[0]
                        cnt = struct.unpack('<i', recv_buffer[21:25])[0]
                        enc1 = struct.unpack('<f', recv_buffer[27:31])[0]
                        force = struct.unpack('<f', recv_buffer[33:37])[0]
                        done = struct.unpack('<i', recv_buffer[39:43])[0]

                        # 데이터 저장
                        self.data['mot_vel'].append(vel)
                        self.data['freq'].append(freq)
                        self.data['cur'].append(current)
                        self.data['cnt'].append(cnt)
                        self.data['enc1'].append(enc1)
                        self.data['force'].append(force)
                        self.data['done'].append(done)

                    except (ValueError, struct.error) as e:
                        print(f"Skipping line due to unpacking error: {line} - Error: {e}")
                        continue

class PlotCanvas(FigureCanvas):
    def __init__(self, data, parent=None):
        fig, self.ax = plt.subplots(7, 1, figsize=(8, 16))
        super(PlotCanvas, self).__init__(fig)
        self.setParent(parent)
        self.data = data    
        if self.is_data_available():
                self.plot_data()
        else:
            print("Data is empty. Plotting skipped.")

    def is_data_available(self):
        # 데이터가 비어있는지 확인
        return any(len(v) > 0 for v in self.data.values())
    def plot_data(self):
        t_data = self.data
        
        # x축을 cnt로 설정 (모든 플롯에 일관적 적용)
        x_axis = t_data['cnt'] if len(t_data['cnt']) > 0 else range(len(t_data['cur']))
        
        self.ax[0].plot(x_axis, t_data['cur'], label='current')
        self.ax[0].set_ylabel('Current (A)')
        self.ax[0].legend()
        print(f'cur plotted: {len(t_data["cur"])} points')

        self.ax[1].plot(x_axis, t_data['mot_vel'], label='mot_vel')
        self.ax[1].set_ylabel('Velocity (rad/s)')
        self.ax[1].legend()

        self.ax[2].plot(x_axis, t_data['force'], label='measured force')
        self.ax[2].plot(x_axis, t_data['ref_force'], label='ref force')
        self.ax[2].set_ylabel('Force (N)')
        self.ax[2].legend()

        self.ax[3].plot(x_axis, t_data['torque'], label='measured torque')
        self.ax[3].set_ylabel('Torque (Nm)')
        self.ax[3].legend()

        self.ax[4].plot(x_axis, t_data['enc1'], label='ankle angle')
        self.ax[4].set_ylabel('Angle (deg)')
        self.ax[4].legend()

        # pMMG 데이터 plot
        self.ax[5].plot(x_axis, t_data['pmmg1'], label='pMMG1')
        self.ax[5].plot(x_axis, t_data['pmmg2'], label='pMMG2')
        self.ax[5].set_ylabel('Pressure (kPa)')
        self.ax[5].legend()

        self.ax[6].plot(x_axis, t_data['gamma'], label='gamma (CCI)', color='purple')
        self.ax[6].set_xlabel('Loop Count (cnt)')
        self.ax[6].set_ylabel('Gamma (CCI)')
        self.ax[6].legend()

        self.draw()

class DataVisualizer(QMainWindow):
    def __init__(self, data):
        super().__init__()
        self.setWindowTitle("Data Visualization")
        self.setGeometry(200, 200, 1000, 800)

        # PlotCanvas 및 NavigationToolbar 추가
        self.canvas = PlotCanvas(data)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)

        # 레이아웃에 캔버스와 툴바 추가
        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

class MainWidget(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CAN FD Data Plotter")
        self.setGeometry(100, 100, 400, 200)

        # 버튼 추가
        self.stop_button = QPushButton("Stop and Load Latest File", self)
        self.stop_button.clicked.connect(self.load_latest_file)
        
        self.plot_button = QPushButton("Plot Figure", self)
        self.plot_button.clicked.connect(self.select_and_plot_file)

        # 레이아웃 설정
        layout = QVBoxLayout()
        layout.addWidget(self.stop_button)
        layout.addWidget(self.plot_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def load_latest_file(self):
        # 가장 최근의 .trc 파일 찾기
        folder_path = "./"  # 필요한 폴더 경로 설정
        list_of_files = glob.glob(os.path.join(folder_path, "*.trc"))
        latest_file = max(list_of_files, key=os.path.getmtime)

        # 데이터 처리 및 시각화 창 열기
        processor = DataProcessor(latest_file)
        processor.load_data()
        self.show_plot_window(processor.data)

    def sysid_load_latest_file(self):
        # 가장 최근의 .trc 파일 찾기
        folder_path = "./"  # 필요한 폴더 경로 설정
        list_of_files = glob.glob(os.path.join(folder_path, "*.trc"))
        latest_file = max(list_of_files, key=os.path.getmtime)

        # 데이터 처리 및 시각화 창 열기
        processor = DataProcessor(latest_file)
        processor.sysid_load_data()
        self.show_plot_window(processor.data)

    def select_and_plot_file(self):
        # 파일 선택 다이얼로그
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Select TRC File", "", "TRC Files (*.trc);;All Files (*)", options=options)
        
        if file_name:
            # 선택한 파일 처리 및 시각화 창 열기
            processor = DataProcessor(file_name)
            processor.load_data()
            self.show_plot_window(processor.data)

    def show_plot_window(self, data):
        # 데이터 시각화를 위한 새 창 열기
        self.plot_window = DataVisualizer(data)
        self.plot_window.show()
