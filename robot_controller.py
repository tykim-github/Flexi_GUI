"""
로봇 제어 관련 기능들
"""

import time
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
        
        # 탭 선택에 따른 루틴
        if hasattr(self.gui_ref, 'tabs'):
            current_tab = self.gui_ref.tabs.currentIndex()
            if current_tab == 0:  # Walking tab
                self.routine_list.append(ROUTINE_ID_MIDLEVEL_ANKLE_REF)
        
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
        msg = [4, pack_sdo_unit(TASK_ID_MSG, SDO_ID_MSG_SET_STATE, SDO_REQU, 1, STATE_STANDBY),
               TASK_ID_MSG, SDO_ID_MSG_PDO_LIST, SDO_REQU, 10,
               TASK_ID_MIDLEVEL, PDO_ID_MIDLEVEL_LOOP_CNT,
               TASK_ID_MIDLEVEL, PDO_ID_MIDLEVEL_REF_POSITION,
               TASK_ID_MIDLEVEL, PDO_ID_MIDLEVEL_LOADCELL_FORCE, # filtered loadcell
               TASK_ID_MIDLEVEL, PDO_ID_MIDLEVEL_ABSENCODER1_POSITION, # ankle angle
               TASK_ID_LOWLEVEL, PDO_ID_LOWLEVEL_CURRENT_OUTPUT,
               TASK_ID_MIDLEVEL, PDO_ID_MIDLEVEL_REF_VELOCITY, 
               TASK_ID_MIDLEVEL, PDO_ID_MIDLEVEL_AC_CTRL_INPUT, # not required
               TASK_ID_MIDLEVEL, PDO_ID_MIDLEVEL_POS_PID_CTRL_INPUT,  # not required
               TASK_ID_MIDLEVEL, PDO_ID_MIDLEVEL_VELOCITY_ESTIMATED,  # not required
               TASK_ID_MIDLEVEL, PDO_ID_MIDLEVEL_LOADCELL_TORQUE,
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

        time.sleep(3)

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
        """로봇 비활성화"""
        msg = [3, pack_sdo_unit(TASK_ID_LOWLEVEL, SDO_ID_LOWLEVEL_SET_STATE, SDO_REQU, 1, STATE_STANDBY),
               pack_sdo_unit(TASK_ID_MIDLEVEL, SDO_ID_MIDLEVEL_SET_STATE, SDO_REQU, 1, STATE_STANDBY),
               pack_sdo_unit(TASK_ID_MSG, SDO_ID_MSG_SET_STATE, SDO_REQU, 1, STATE_STANDBY)]
        msg = flatten_list(msg)
        self.pcan_comm.send_message(msg, SDO, self.node_id)

        msg = [1, pack_sdo_unit(TASK_ID_MSG, SDO_ID_MSG_SET_STATE, SDO_REQU, 1, STATE_STANDBY)]
        msg = flatten_list(msg)
        self.pcan_comm.send_message(msg, SDO, self.node_id)

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
