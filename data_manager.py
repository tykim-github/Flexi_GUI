"""
Data management for GUI - handles data capture, loading, saving, and plotting
"""

import glob
import os
import numpy as np
from plot_graph import DataProcessor, DataVisualizer


class DataManager:
    """데이터 캡처, 저장, 로드 관리"""
    
    def __init__(self, pcan_communicator):
        """
        초기화
        
        Parameters:
            pcan_communicator: PCAN 통신 객체
        """
        self.pcan_comm = pcan_communicator
        self.data = {}
        self.output_filename = ''
        self.m_thread_run = False
        self.m_obj_thread = None
        
        # Trace settings
        self.trace_file_single = True
        self.trace_file_date = True
        self.trace_file_time = True
        self.trace_file_overwrite = False
        self.trace_file_data_length = False
        self.trace_file_size = 100
        self.trace_path = b''

    def configure_and_start_trace(self):
        """트레이싱 설정 및 시작"""
        if self.pcan_comm.configure_trace(
            self.trace_path, self.trace_file_size,
            self.trace_file_single, self.trace_file_date,
            self.trace_file_time, self.trace_file_overwrite,
            self.trace_file_data_length):
            
            if self.pcan_comm.start_trace():
                self.m_obj_thread = self.pcan_comm._thread if hasattr(self.pcan_comm, '_thread') else None
                self.m_thread_run = True
                return True
        return False

    def stop_trace(self):
        """트레이싱 중지"""
        self.pcan_comm.stop_trace()
        self.m_thread_run = False
        if self.m_obj_thread:
            self.m_obj_thread.join()

    def load_latest_trc_file(self, node_id=0x07):
        """가장 최근의 .trc 파일 로드"""
        try:
            folder_path = "./"
            list_of_files = glob.glob(os.path.join(folder_path, "*.trc"))
            if not list_of_files:
                return False
            
            filename = max(list_of_files, key=os.path.getmtime)
            processor = DataProcessor(filename, node_id=node_id)
            processor.load_data()
            self.data = processor.data
            return True
        except Exception as e:
            print(f"Error loading file: {e}")
            return False

    def load_sysid_trc_file(self, node_id=0x07):
        """System ID 트레이싱 파일 로드"""
        try:
            folder_path = "./"
            list_of_files = glob.glob(os.path.join(folder_path, "*.trc"))
            if not list_of_files:
                return False
            
            filename = max(list_of_files, key=os.path.getmtime)
            processor = DataProcessor(filename, node_id=node_id)
            processor.sysid_load_data()
            self.data = processor.data
            return True
        except Exception as e:
            print(f"Error loading sysid file: {e}")
            return False

    def save_to_txt(self, filename=None):
        """
        데이터를 텍스트 파일로 저장 (일반 데이터 + pMMG)
        
        Parameters:
            filename: 저장할 파일명 (None이면 self.output_filename 사용)
        """
        save_filename = filename if filename else self.output_filename
        
        if not save_filename:
            print("No filename specified")
            return False
            
        if not any(len(v) > 0 for v in self.data.values()):
            print("No data to save.")
            return False

        try:
            # pMMG 데이터가 있으면 포함, 없으면 제외
            if len(self.data.get('pmmg1', [])) > 0:
                data_array = np.column_stack([
                    self.data['cnt'], self.data['ref_torque'], self.data['force'],
                    self.data['enc1'], self.data['cur'], self.data['ref_vel'],
                    self.data['mot_vel'], self.data['torque'], self.data['pmmg1'], self.data['pmmg2']
                ])
                header = "cnt ref_torque force enc1 cur ref_vel mot_vel torque pmmg1 pmmg2"
            else:
                data_array = np.column_stack([
                    self.data['cnt'], self.data['ref_torque'], self.data['force'],
                    self.data['enc1'], self.data['cur'], self.data['ref_vel'],
                    self.data['mot_vel'], self.data['torque']
                ])
                header = "cnt ref_torque force enc1 cur ref_vel mot_vel torque"
            
            np.savetxt(save_filename, data_array, header=header, fmt='%.6f', delimiter='\t')
            print(f"Data saved to {save_filename}")
            return True
        except Exception as e:
            print(f"Error saving data: {e}")
            return False

    def save_sysid_to_txt(self, filename=None):
        """
        데이터를 텍스트 파일로 저장 (System ID 데이터)
        
        Parameters:
            filename: 저장할 파일명
        """
        if not filename:
            print("No filename specified")
            return False
            
        if not any(len(v) > 0 for v in self.data.values()):
            print("No data to save.")
            return False

        try:
            data_array = np.column_stack([
                self.data['cnt'], self.data['freq'], self.data['cur'],
                self.data['force'], self.data['enc1'], self.data['mot_vel']
            ])
            header = "cnt freq cur force enc1 motor_vel"
            np.savetxt(filename + '.txt', data_array, header=header, fmt='%.6f', delimiter='\t')
            print(f"Data saved to {filename + '.txt'}")
            return True
        except Exception as e:
            print(f"Error saving sysid data: {e}")
            return False

    def generate_output_filename(self, trc_filename, control_flags, parameters):
        """
        출력 파일명 생성
        
        Parameters:
            trc_filename: 원본 .trc 파일명
            control_flags: {'PD': bool, 'FF': bool, 'DOB': bool, 'LS': bool, 'Fric': bool}
            parameters: {'Kp': str, 'Kd': str, 'T1': str, 'T2': str, 'T3': str}
        
        Returns:
            생성된 파일명
        """
        # trc 파일의 이름에서 날짜/시간 부분 제거
        output_filename = trc_filename[:-19]
        
        # 활성화된 제어 옵션 추가
        if control_flags.get('PD', False):
            output_filename += '_PD'
        if control_flags.get('FF', False):
            output_filename += '_FF'
        if control_flags.get('DOB', False):
            output_filename += '_DOB'
        if control_flags.get('LS', False):
            output_filename += '_LS'
        if control_flags.get('Fric', False):
            output_filename += '_Fric'
        
        # 파라미터 추가
        output_filename += f"_Kp{parameters.get('Kp', '0')}"
        output_filename += f"_Kd{parameters.get('Kd', '0')}"
        output_filename += f"_T{parameters.get('T1', '0')}"
        output_filename += f"_P{parameters.get('T2', '0')}"
        output_filename += f"_R{parameters.get('T3', '0')}"
        output_filename += f"_W{parameters.get('T3', '0')}"
        output_filename += '.txt'
        
        return output_filename

    def show_plot(self):
        """데이터 플롯 표시"""
        try:
            plot_window = DataVisualizer(self.data)
            plot_window.show()
            return plot_window
        except Exception as e:
            print(f"Error showing plot: {e}")
            return None

    def save_to_txt_with_data(self, data, filename=None):
        """
        주어진 데이터를 텍스트 파일로 저장
        
        Parameters:
            data: 저장할 데이터 딕셔너리
            filename: 저장할 파일명
        
        Returns:
            저장된 파일명
        """
        save_filename = filename if filename else self.output_filename
        
        if not save_filename:
            print("No filename specified")
            return None
            
        if not any(len(v) > 0 for v in data.values()):
            print("No data to save.")
            return None

        try:
            # 사용 가능한 데이터 키 확인
            available_keys = []
            data_columns = []
            
            column_order = ['cnt', 'ref_torque', 'force', 'enc1', 'cur', 'ref_vel', 'AC', 'FB', 'mot_vel', 'torque']
            for key in column_order:
                if key in data and len(data[key]) > 0:
                    available_keys.append(key)
                    data_columns.append(data[key])
            
            if not data_columns:
                print("No valid data columns to save.")
                return None
            
            data_array = np.column_stack(data_columns)
            header = " ".join(available_keys)
            np.savetxt(save_filename, data_array, header=header, fmt='%.6f', delimiter='\t')
            print(f"Data saved to {save_filename}")
            return save_filename
        except Exception as e:
            print(f"Error saving data: {e}")
            return None

    def capture_sysid_data(self):
        """System ID 데이터 캡처 시작"""
        self.m_thread_run = True
        if self.pcan_comm:
            self.pcan_comm.start_trace()
        return True

    def stop_sysid_data(self):
        """System ID 데이터 캡처 중지"""
        self.m_thread_run = False
        if self.pcan_comm:
            self.pcan_comm.stop_trace()
        return True

    def get_latest_file(self, file_pattern="*.trc"):
        """
        지정된 패턴의 가장 최신 파일 가져오기
        
        Parameters:
            file_pattern: 파일 패턴 (예: "*.trc", "*sysid*.txt")
        
        Returns:
            파일명 또는 None
        """
        try:
            folder_path = "./"
            list_of_files = glob.glob(os.path.join(folder_path, file_pattern))
            if not list_of_files:
                return None
            
            return max(list_of_files, key=os.path.getmtime)
        except Exception as e:
            print(f"Error getting latest file: {e}")
            return None