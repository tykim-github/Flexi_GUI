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
    def __init__(self, filename):
        self.filename = filename
        self.data = {'cnt': [], 'ref_torque': [], 'torque': [], 'gait_phase': [], 
                     'enc1': [], 'enc2': [], 'dist': [], 'cur': [], 'FB': [], 'FF': [], 'gait_phase_widm': [], 'gait_period': [],
                     'freq':[],'mot_vel':[], 'force':[], 'done':[],'ref_vel':[],'AC':[]}
    
    def load_data(self):
        with open(self.filename, 'r') as file:
            lines = file.readlines()[34:]  # Skip header lines
            # cnt_pre=0
            for line in lines:
                if 'Rx' in line and '0361' in line:
                    try:
                        # 'Rx' 위치를 찾고 데이터를 추출
                        index = line.index('Rx') + 5
                        hex_data = line[index:].split()  # Index 이후부터 데이터 추출
                        
                        # 한 줄의 데이터를 합쳐서 hex로 변환
                        hex_str = ''.join(hex_data)
                        
                        # hex 데이터를 byte로 변환
                        recv_buffer = bytes.fromhex(hex_str)
                        
                        # 데이터 변환 - 오프셋에 따른 정확한 데이터 추출
                        cnt = struct.unpack('<i', recv_buffer[3:7])[0]
                        ref_torque = struct.unpack('<f', recv_buffer[9:13])[0]
                        force = struct.unpack('<f', recv_buffer[15:19])[0]
                        enc1 = struct.unpack('<f', recv_buffer[21:25])[0]
                        cur = struct.unpack('<f', recv_buffer[27:31])[0]
                        ref_vel = struct.unpack('<f', recv_buffer[33:37])[0]
                        AC = struct.unpack('<f', recv_buffer[39:43])[0]
                        FB = struct.unpack('<f', recv_buffer[45:49])[0]
                        mot_vel = struct.unpack('<f', recv_buffer[51:55])[0]
                        torque = struct.unpack('<f', recv_buffer[57:61])[0]
                        # torque = struct.unpack('<f', recv_buffer[63:67])[0]

                        # 데이터 저장
                        self.data['cnt'].append(cnt)
                        self.data['ref_torque'].append(ref_torque)
                        self.data['force'].append(force)
                        self.data['enc1'].append(enc1)
                        self.data['cur'].append(cur)
                        self.data['ref_vel'].append(ref_vel)
                        self.data['AC'].append(AC)
                        self.data['FB'].append(FB)
                        self.data['mot_vel'].append(mot_vel)
                        self.data['torque'].append(torque)
                        # self.data['torque'].append(torque)
                        
                        

                    except (ValueError, struct.error) as e:
                        print(f"Skipping line due to unpacking error: {line} - Error: {e}")
                        continue

    def sysid_load_data(self):
        with open(self.filename, 'r') as file:
            lines = file.readlines()[34:]  # Skip header lines
            # cnt_pre=0
            for line in lines:
                if 'Rx' in line and '0361' in line:
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
        fig, self.ax = plt.subplots(5, 1, figsize=(8, 12))
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
        
        self.ax[0].plot(t_data['cur'], label='current')
        self.ax[0].legend()
        print('cur plotted')

        self.ax[1].plot(t_data['mot_vel'],label='mot_vel')
        self.ax[1].legend()

        self.ax[2].plot(t_data['force'], label='load cell')
        self.ax[2].plot(t_data['ref_torque'], label='ref')
        self.ax[2].legend()

        self.ax[3].plot(t_data['torque'], label='freq')
        self.ax[3].legend()

        self.ax[4].plot(t_data['enc1'], label='impedance_ref')
        self.ax[4].legend()

        # self.ax[2].plot(t_data['cur'], label='cur')
        # self.ax[2].plot(t_data['dist'], label='dist')
        # self.ax[2].plot(t_data['FB'], label='FB')
        # self.ax[2].legend()

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
