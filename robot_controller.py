"""
로봇 제어 관련 기능들
"""

import time
import threading
from constants import *
from message_handler import pack_sdo_unit, flatten_list, float_to_byte_list


class RobotController:
    """로봇 제어 클래스"""
    
    def __init__(self, pcan_communicator, node_id=0x07):
        """
        초기화
        
        Parameters:
            pcan_communicator: PCAN 통신 객체
            node_id: 노드 ID
        """
        self.pcan_comm = pcan_communicator
        self.node_id = node_id
        self.routine_list = []
        self.gui_ref = None
        self.pmmg_monitoring_active = False
        self.pmmg_receive_thread = None

    def _send_message(self, msg):
        """메시지 전송"""
        if self.pcan_comm is None or self.pcan_comm.obj_pcan_basic is None:
            print("PCAN not initialized")
            return False
        msg = flatten_list(msg)
        return self.pcan_comm.send_message(msg, SDO, self.node_id)

    def set_gui_reference(self, gui_ref):
        """GUI 참조 설정"""
        self.gui_ref = gui_ref

    def _build_routine_list(self):
        """체크박스 상태에 따라 루틴 리스트 구성"""
        self.routine_list = [ROUTINE_ID_MIDLEVEL_RISK_MANAGEMENT]
        
        if self.gui_ref is None:
            return
        
        # 파라미터 탭 선택에 따른 루틴
        if hasattr(self.gui_ref, 'ui_builder') and hasattr(self.gui_ref.ui_builder, 'tabs'):
            param_tab = self.gui_ref.ui_builder.tabs.get('ref')
            if param_tab is not None:
                current_param_tab = param_tab.currentIndex()
                if current_param_tab == 0:  # Walking tab
                    self.routine_list.append(ROUTINE_ID_MIDLEVEL_ANKLE_REF)
                elif current_param_tab == 1:  # Sine tab
                    self.routine_list.append(ROUTINE_ID_MIDLEVEL_POSITION_SINE_REF)
                elif current_param_tab == 2:  # Square tab
                    self.routine_list.append(ROUTINE_ID_MIDLEVEL_POSITION_TANH_REF)
                elif current_param_tab == 3:  # Ankle tab
                    self.routine_list.append(ROUTINE_ID_MIDLEVEL_ANKLE_REF_PERIODIC)
                elif current_param_tab == 4:  # SAAN tab
                    self.routine_list.append(ROUTINE_ID_MIDLEVEL_PROPORTIONAL_ASSIST)
        
        # 체크박스 기반 루틴
        if hasattr(self.gui_ref, 'checkboxes_dict'):
            checkboxes = self.gui_ref.checkboxes_dict
            
            if checkboxes.get('PD') and checkboxes['PD'].isChecked():
                self.routine_list.append(ROUTINE_ID_MIDLEVEL_POSITION_CTRL)
            if checkboxes.get('FF') and checkboxes['FF'].isChecked():
                self.routine_list.append(ROUTINE_ID_MIDLEVEL_FEEDFORWARD_FILTER)
            if checkboxes.get('DOB') and checkboxes['DOB'].isChecked():
                self.routine_list.append(ROUTINE_ID_MIDLEVEL_DISTURBANCE_OBS)
            if checkboxes.get('LS') and checkboxes['LS'].isChecked():
                self.routine_list.append(ROUTINE_ID_MIDLEVEL_VELOCITY_CTRL)
            if checkboxes.get('Fric') and checkboxes['Fric'].isChecked():
                self.routine_list.append(ROUTINE_ID_MIDLEVEL_ANKLE_COMPENSATOR)

    def init_torque(self):
        """토크 초기화"""
        msg = [1, pack_sdo_unit(TASK_ID_MIDLEVEL, SDO_ID_MIDLEVEL_INIT_TORQUE, 
                               SDO_REQU, 1, 1)]
        msg = flatten_list(msg)
        self.pcan_comm.send_message(msg, SDO, self.node_id)

    def robot_on(self, get_routine_list_func=None, get_data_func=None):
        """
        로봇 활성화
        
        Parameters:
            get_routine_list_func: (Optional) 루틴 리스트를 얻는 함수
            get_data_func: (Optional) 데이터 얻는 함수
        """
        # pMMG 선택: LEFT(0x06)면 pMMG1,2 / RIGHT(0x07)면 pMMG3,4
        if self.node_id == 0x06:
            pmmg_id1 = PDO_ID_MIDLEVEL_PMMG1  # 0x22
            pmmg_id2 = PDO_ID_MIDLEVEL_PMMG2  # 0x23
        else:
            pmmg_id1 = PDO_ID_MIDLEVEL_PMMG3  # 0x24
            pmmg_id2 = PDO_ID_MIDLEVEL_PMMG4  # 0x0B
        
        msg = [4, pack_sdo_unit(TASK_ID_MSG, SDO_ID_MSG_SET_STATE, SDO_REQU, 1, STATE_STANDBY),
               TASK_ID_MSG, SDO_ID_MSG_PDO_LIST, SDO_REQU, 10,
               TASK_ID_MIDLEVEL, PDO_ID_MIDLEVEL_LOOP_CNT,
               TASK_ID_MIDLEVEL, PDO_ID_MIDLEVEL_REF_POSITION,
               TASK_ID_MIDLEVEL, PDO_ID_MIDLEVEL_LOADCELL_FORCE, # filtered loadcell
               TASK_ID_MIDLEVEL, PDO_ID_MIDLEVEL_ABSENCODER1_POSITION, # ankle angle
               TASK_ID_LOWLEVEL, PDO_ID_LOWLEVEL_CURRENT_OUTPUT,
               TASK_ID_MIDLEVEL, PDO_ID_MIDLEVEL_REF_VELOCITY, 
               TASK_ID_MIDLEVEL, PDO_ID_MIDLEVEL_LOADCELL_TORQUE,
               TASK_ID_MIDLEVEL, pmmg_id1,  # pMMG 1 (LEFT: pMMG1, RIGHT: pMMG3)
               TASK_ID_MIDLEVEL, pmmg_id2,  # pMMG 2 (LEFT: pMMG2, RIGHT: pMMG4)
               TASK_ID_MIDLEVEL, PDO_ID_MIDLEVEL_GAMMA,  # Gamma (CCI)
               pack_sdo_unit(TASK_ID_MSG, SDO_ID_MSG_GUI_COMM_ONOFF, SDO_REQU, 1, 0),
               pack_sdo_unit(TASK_ID_MSG, SDO_ID_MSG_GUI_COMM_COMMAND, SDO_REQU, 1, MECH_SYS_ID_SBS_RAW_DATA)]
        msg = flatten_list(msg)
        self.pcan_comm.send_message(msg, SDO, self.node_id)

        # State transition to Enable
        msg = [3, pack_sdo_unit(TASK_ID_MSG, SDO_ID_MSG_SET_ROUTINE, SDO_REQU, 1, ROUTINE_ID_MSG_PDO_SEND),
               pack_sdo_unit(TASK_ID_LOWLEVEL, SDO_ID_LOWLEVEL_SET_STATE, SDO_REQU, 1, STATE_ENABLE),
               pack_sdo_unit(TASK_ID_LOWLEVEL, SDO_ID_LOWLEVEL_SET_ROUTINE, SDO_REQU, 1, ROUTINE_ID_LOWLEVEL_CURRENT_CTRL)]
        msg = flatten_list(msg)
        self.pcan_comm.send_message(msg, SDO, self.node_id)

        time.sleep(0.05)

        # 루틴 리스트 구성 - 콜백 함수가 있으면 사용, 아니면 GUI 상태에서 구성
        if get_routine_list_func is not None:
            self.routine_list = get_routine_list_func()
        else:
            self._build_routine_list()

        msg = [3, pack_sdo_unit(TASK_ID_MSG, SDO_ID_MSG_SET_STATE, SDO_REQU, 1, STATE_ENABLE),
               pack_sdo_unit(TASK_ID_MIDLEVEL, SDO_ID_MIDLEVEL_SET_STATE, SDO_REQU, 1, STATE_ENABLE),
               pack_sdo_unit(TASK_ID_MIDLEVEL, SDO_ID_MIDLEVEL_SET_ROUTINE, SDO_REQU, len(self.routine_list), self.routine_list)]
        msg = flatten_list(msg)
        self.pcan_comm.send_message(msg, SDO, self.node_id)

    def robot_off(self):
        """
        로봇 비활성화 (안전한 종료)
        
        전송 순서:
        1. Assist OFF (모든 제어 입력 중단)
        2. MIDLEVEL 루틴 중단 (empty routine)
        3. LOWLEVEL state → Standby (전류 제어 중단, Gate OFF)
        4. MIDLEVEL state → Standby (모든 제어 입력 초기화)
        5. MSG state → Standby (메시지 중단)
        """
        try:
            # Step 1: Assist OFF (안전성 확보)
            msg = [1, pack_sdo_unit(TASK_ID_MIDLEVEL, SDO_ID_MIDLEVEL_ASSIST_ONOFF, SDO_REQU, 1, 0)]
            msg = flatten_list(msg)
            self.pcan_comm.send_message(msg, SDO, self.node_id)
            time.sleep(0.05)
            
            # Step 2: MIDLEVEL 루틴 중단 (empty routine list)
            msg = [1, pack_sdo_unit(TASK_ID_MIDLEVEL, SDO_ID_MIDLEVEL_SET_ROUTINE, SDO_REQU, 1, 
                                   [ROUTINE_ID_MIDLEVEL_RISK_MANAGEMENT])]
            msg = flatten_list(msg)
            self.pcan_comm.send_message(msg, SDO, self.node_id)
            time.sleep(0.05)
            
            # Step 3: LOWLEVEL state → Standby (Gate driver OFF, PWM 중지)
            msg = [1, pack_sdo_unit(TASK_ID_LOWLEVEL, SDO_ID_LOWLEVEL_SET_STATE, SDO_REQU, 1, STATE_STANDBY)]
            msg = flatten_list(msg)
            self.pcan_comm.send_message(msg, SDO, self.node_id)
            time.sleep(0.05)
            
            # Step 4: MIDLEVEL state → Standby (모든 제어 입력 초기화 수행)
            msg = [1, pack_sdo_unit(TASK_ID_MIDLEVEL, SDO_ID_MIDLEVEL_SET_STATE, SDO_REQU, 1, STATE_STANDBY)]
            msg = flatten_list(msg)
            self.pcan_comm.send_message(msg, SDO, self.node_id)
            time.sleep(0.05)
            
            # Step 5: MSG state → Standby (메시지 송수신 중단)
            msg = [1, pack_sdo_unit(TASK_ID_MSG, SDO_ID_MSG_SET_STATE, SDO_REQU, 1, STATE_STANDBY)]
            msg = flatten_list(msg)
            self.pcan_comm.send_message(msg, SDO, self.node_id)
            
            print("Robot OFF completed successfully")
        except Exception as e:
            print(f"Robot OFF error: {str(e)}")

    def assist_on(self):
        """어시스턴스 활성화"""
        msg = [1, pack_sdo_unit(TASK_ID_MIDLEVEL, SDO_ID_MIDLEVEL_ASSIST_ONOFF, SDO_REQU, 1, 1)]
        msg = flatten_list(msg)
        self.pcan_comm.send_message(msg, SDO, self.node_id)

    def assist_off(self):
        """어시스턴스 비활성화"""
        msg = [1, pack_sdo_unit(TASK_ID_MIDLEVEL, SDO_ID_MIDLEVEL_ASSIST_ONOFF, SDO_REQU, 1, 0)]
        msg = flatten_list(msg)
        self.pcan_comm.send_message(msg, SDO, self.node_id)

    def test(self, get_routine_list_func=None):
        """테스트 실행"""
        msg = [4, pack_sdo_unit(TASK_ID_MSG, SDO_ID_MSG_SET_STATE, SDO_REQU, 1, STATE_STANDBY),
               TASK_ID_MSG, SDO_ID_MSG_PDO_LIST, SDO_REQU, 9,
               TASK_ID_MIDLEVEL, PDO_ID_MIDLEVEL_LOOP_CNT,
               TASK_ID_MIDLEVEL, PDO_ID_MIDLEVEL_REF_IMPEDANCE,
               TASK_ID_MIDLEVEL, PDO_ID_MIDLEVEL_LOADCELL_FORCE,
               TASK_ID_MIDLEVEL, PDO_ID_MIDLEVEL_ABSENCODER1_POSITION,
               TASK_ID_LOWLEVEL, PDO_ID_LOWLEVEL_CURRENT_OUTPUT,
               TASK_ID_MIDLEVEL, PDO_ID_MIDLEVEL_DOB_DISTURABNCE,
               TASK_ID_MIDLEVEL, PDO_ID_MIDLEVEL_FF_INPUT,
               TASK_ID_MIDLEVEL, PDO_ID_MIDLEVEL_POS_PID_CTRL_INPUT,
               TASK_ID_WIDM, PDO_ID_WIDM_GAIT_PHASE,
               pack_sdo_unit(TASK_ID_MSG, SDO_ID_MSG_GUI_COMM_ONOFF, SDO_REQU, 1, 0),
               pack_sdo_unit(TASK_ID_MSG, SDO_ID_MSG_GUI_COMM_COMMAND, SDO_REQU, 1, MECH_SYS_ID_SBS_RAW_DATA)]
        msg = flatten_list(msg)
        self.pcan_comm.send_message(msg, SDO, self.node_id)

        msg = [1, pack_sdo_unit(TASK_ID_MSG, SDO_ID_MSG_SET_ROUTINE, SDO_REQU, 1, ROUTINE_ID_MSG_PDO_SEND)]
        msg = flatten_list(msg)
        self.pcan_comm.send_message(msg, SDO, self.node_id)
        
        time.sleep(2)
        
        # 루틴 리스트 구성 - 콜백 함수가 있으면 사용, 아니면 GUI 상태에서 구성
        if get_routine_list_func is not None:
            self.routine_list = get_routine_list_func()
        else:
            self._build_routine_list()

        msg = [3, pack_sdo_unit(TASK_ID_MSG, SDO_ID_MSG_SET_STATE, SDO_REQU, 1, STATE_ENABLE),
               pack_sdo_unit(TASK_ID_MIDLEVEL, SDO_ID_MIDLEVEL_SET_STATE, SDO_REQU, 1, STATE_ENABLE),
               pack_sdo_unit(TASK_ID_MIDLEVEL, SDO_ID_MIDLEVEL_SET_ROUTINE, SDO_REQU, len(self.routine_list), self.routine_list)]
        msg = flatten_list(msg)
        self.pcan_comm.send_message(msg, SDO, self.node_id)

    def start_pmmg_monitor(self):
        """pMMG 실시간 모니터링 시작 (mid-level enabled)"""
        try:
            if self.pcan_comm is None or self.pcan_comm.obj_pcan_basic is None:
                print("PCAN not initialized")
                return False
            
            # pMMG ID 설정: LEFT(0x06)면 pMMG1,2 / RIGHT(0x07)면 pMMG3,4
            if self.node_id == 0x06:
                pmmg_id1 = PDO_ID_MIDLEVEL_PMMG1  # 0x22
                pmmg_id2 = PDO_ID_MIDLEVEL_PMMG2  # 0x23
            else:
                pmmg_id1 = PDO_ID_MIDLEVEL_PMMG3  # 0x24
                pmmg_id2 = PDO_ID_MIDLEVEL_PMMG4  # 0x0B
            
            # Step 1: MSG state -> Standby
            msg = [1, pack_sdo_unit(TASK_ID_MSG, SDO_ID_MSG_SET_STATE, SDO_REQU, 1, STATE_STANDBY)]
            msg = flatten_list(msg)
            self.pcan_comm.send_message(msg, SDO, self.node_id)
            time.sleep(0.05)
            
            # Step 2: PDO list 설정 (cnt, pmmg1, pmmg2, ankle_angle, gamma)
            msg = [2, TASK_ID_MSG, SDO_ID_MSG_PDO_LIST, SDO_REQU, 5,
                   TASK_ID_MIDLEVEL, PDO_ID_MIDLEVEL_LOOP_CNT,
                   TASK_ID_MIDLEVEL, pmmg_id1,
                   TASK_ID_MIDLEVEL, pmmg_id2,
                   TASK_ID_MIDLEVEL, PDO_ID_MIDLEVEL_ABSENCODER1_POSITION,
                   TASK_ID_MIDLEVEL, PDO_ID_MIDLEVEL_GAMMA,
                   pack_sdo_unit(TASK_ID_MSG, SDO_ID_MSG_GUI_COMM_ONOFF, SDO_REQU, 1, 0),
                   pack_sdo_unit(TASK_ID_MSG, SDO_ID_MSG_GUI_COMM_COMMAND, SDO_REQU, 1, 0)]
            msg = flatten_list(msg)
            self.pcan_comm.send_message(msg, SDO, self.node_id)
            time.sleep(0.05)
            
            # Step 3: MSG routine -> PDO_SEND
            msg = [1, pack_sdo_unit(TASK_ID_MSG, SDO_ID_MSG_SET_ROUTINE, SDO_REQU, 1, ROUTINE_ID_MSG_PDO_SEND)]
            msg = flatten_list(msg)
            self.pcan_comm.send_message(msg, SDO, self.node_id)
            time.sleep(0.05)
            
            # Step 4: MSG state -> Enable
            msg = [1, pack_sdo_unit(TASK_ID_MSG, SDO_ID_MSG_SET_STATE, SDO_REQU, 1, STATE_ENABLE)]
            msg = flatten_list(msg)
            self.pcan_comm.send_message(msg, SDO, self.node_id)
            time.sleep(0.05)
            
            # Step 5: MIDLEVEL state -> Standby
            msg = [1, pack_sdo_unit(TASK_ID_MIDLEVEL, SDO_ID_MIDLEVEL_SET_STATE, SDO_REQU, 1, STATE_STANDBY)]
            msg = flatten_list(msg)
            self.pcan_comm.send_message(msg, SDO, self.node_id)
            time.sleep(0.05)
            
            # Step 6: MIDLEVEL state -> Enable
            msg = [1, pack_sdo_unit(TASK_ID_MIDLEVEL, SDO_ID_MIDLEVEL_SET_STATE, SDO_REQU, 1, STATE_ENABLE)]
            msg = flatten_list(msg)
            self.pcan_comm.send_message(msg, SDO, self.node_id)
            time.sleep(0.05)
            
            self.pmmg_monitoring_active = True
            return True
        except Exception as e:
            print(f"Start pMMG monitor failed: {str(e)}")
            return False

    def stop_pmmg_monitor(self):
        """pMMG 실시간 모니터링 중지"""
        try:
            if self.pcan_comm is None or self.pcan_comm.obj_pcan_basic is None:
                print("PCAN not initialized")
                return False
            
            self.pmmg_monitoring_active = False
            
            # MIDLEVEL state -> Standby
            msg = [1, pack_sdo_unit(TASK_ID_MIDLEVEL, SDO_ID_MIDLEVEL_SET_STATE, SDO_REQU, 1, STATE_STANDBY)]
            msg = flatten_list(msg)
            self.pcan_comm.send_message(msg, SDO, self.node_id)
            time.sleep(0.5)
            
            # MSG state -> Standby
            msg = [1, pack_sdo_unit(TASK_ID_MSG, SDO_ID_MSG_SET_STATE, SDO_REQU, 1, STATE_STANDBY)]
            msg = flatten_list(msg)
            self.pcan_comm.send_message(msg, SDO, self.node_id)
            
            return True
        except Exception as e:
            print(f"Stop pMMG monitor failed: {str(e)}")
            return False

    def get_pmmg_monitoring_status(self):
        """pMMG 모니터링 상태 반환"""
        return self.pmmg_monitoring_active

    def start_pmmg_receive_loop(self, data_emitter=None):
        """pMMG 데이터 수신 루프 시작 (백그라운드 스레드)"""
        if self.pmmg_receive_thread is not None and self.pmmg_receive_thread.is_alive():
            print("pMMG receive loop already running")
            return False
        
        self.pmmg_receive_thread = threading.Thread(
            target=self._pmmg_receive_loop_worker, 
            args=(data_emitter,), 
            daemon=True
        )
        self.pmmg_receive_thread.start()
        return True

    def _pmmg_receive_loop_worker(self, data_emitter=None):
        """백그라운드 스레드에서 실행: pMMG 데이터 수신 처리"""
        try:
            import struct
            
            # 우리 노드의 PDO 메시지 ID
            expected_can_id = 0x0361 if self.node_id == 0x06 else 0x0371
            
            while self.pmmg_monitoring_active:
                if self.pcan_comm is None or self.pcan_comm.obj_pcan_basic is None:
                    break
                
                # 모든 대기 중인 메시지 읽기
                messages = self.pcan_comm.read_all_messages()
                
                for msg in messages:
                    try:
                        # CAN ID 필터링
                        if msg.ID != expected_can_id:
                            continue
                        
                        # TPCANMsgFD 객체에서 데이터 추출
                        data_bytes = bytes(msg.DATA[:msg.DLC * 8])
                        
                        # 메시지 형식: [count, task_id, pdo_id, data(4), task_id, pdo_id, data(4), ...]
                        if len(data_bytes) < 1:
                            continue
                        
                        count = data_bytes[0]
                        
                        # 필요한 PDO_ID 결정 (node_id별)
                        if self.node_id == 0x06:  # LEFT
                            required_pdo_ids = [0x00, 0x22, 0x23, 0x0C, 0x20]  # LOOP_CNT, PMMG1, PMMG2, ABSENCODER1, GAMMA
                        else:  # RIGHT (0x07)
                            required_pdo_ids = [0x00, 0x24, 0x0B, 0x0C, 0x20]  # LOOP_CNT, PMMG3, PMMG4, ABSENCODER1, GAMMA
                        
                        # PDO 파싱
                        pdo_data = {}
                        offset = 1
                        
                        for i in range(count):
                            if offset + 6 > len(data_bytes):
                                break
                            
                            pdo_id = data_bytes[offset + 1]
                            
                            # 필요한 PDO_ID만 처리
                            if pdo_id in required_pdo_ids:
                                if pdo_id == 0x00:  # LOOP_CNT (uint32)
                                    pdo_data['cnt'] = struct.unpack('<I', data_bytes[offset + 2:offset + 6])[0]
                                elif pdo_id == 0x0C:  # ABSENCODER1_POSITION (float)
                                    pdo_data['ankle_angle'] = struct.unpack('<f', data_bytes[offset + 2:offset + 6])[0]
                                elif pdo_id == 0x20:  # GAMMA (float)
                                    pdo_data['gamma'] = struct.unpack('<f', data_bytes[offset + 2:offset + 6])[0]
                                else:  # PMMG (float)
                                    pmmg_val = struct.unpack('<f', data_bytes[offset + 2:offset + 6])[0]
                                    if pdo_id == 0x22:  # PMMG1 (LEFT)
                                        pdo_data['pmmg1'] = pmmg_val
                                    elif pdo_id == 0x23:  # PMMG2 (LEFT)
                                        pdo_data['pmmg2'] = pmmg_val
                                    elif pdo_id == 0x24:  # PMMG3 (RIGHT)
                                        pdo_data['pmmg1'] = pmmg_val
                                    elif pdo_id == 0x0B:  # PMMG4 (RIGHT)
                                        pdo_data['pmmg2'] = pmmg_val
                            
                            offset += 6
                        
                        # 5개 모두 있으면 신호 발송
                        if 'cnt' in pdo_data and 'pmmg1' in pdo_data and 'pmmg2' in pdo_data and 'ankle_angle' in pdo_data and 'gamma' in pdo_data:
                            if data_emitter is not None:
                                data_emitter.data_ready.emit(
                                    float(pdo_data['cnt']),
                                    float(pdo_data['pmmg1']),
                                    float(pdo_data['pmmg2']),
                                    float(pdo_data['ankle_angle']),
                                    float(pdo_data['gamma'])
                                )
                    except Exception:
                        pass
                
                time.sleep(0.001)
        except Exception:
            pass
