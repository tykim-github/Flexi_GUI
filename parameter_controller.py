"""
Parameter control - handles setting parameters for various control modes
"""

from constants import *
from message_handler import pack_sdo_unit, flatten_list, float_to_byte_list


class ParameterController:
    """파라미터 설정 및 제어"""
    
    def __init__(self, pcan_communicator, node_id=0x07):
        """
        초기화
        
        Parameters:
            pcan_communicator: PCAN 통신 객체
            node_id: 노드 ID
        """
        self.pcan_comm = pcan_communicator
        self.node_id = node_id
        self.gui_ref = None

    def set_gui_reference(self, gui_ref):
        """GUI 참조 설정"""
        self.gui_ref = gui_ref

    def _send_message(self, msg):
        """메시지 전송"""
        msg = flatten_list(msg)
        return self.pcan_comm.send_message(msg, SDO, self.node_id)

    def set_control_parameters(self, **kwargs):
        """
        제어 파라미터 설정 (키워드 기반)
        
        Parameters:
            kp, kd, sat, max_error, max_rom, min_rom, 
            imp_kp, imp_kd, imp_lambda, imp_epsilon
        """
        kp = kwargs.get('Kp', 0.2)
        kd = kwargs.get('Kd', 0.0001)
        sat = kwargs.get('Limit', 6)
        max_error = kwargs.get('Max_error', 30)
        max_rom = kwargs.get('Max_ank_ang', 20)
        min_rom = kwargs.get('Min_ank_ang', -35)
        imp_kp = kwargs.get('imp_kp', 11.73)
        imp_kd = kwargs.get('imp_kd', 0.83)
        imp_lambda = kwargs.get('imp_lambda', 0)
        imp_epsilon = kwargs.get('imp_epsilon', 0)
        
        # Risk parameters
        msg = [1, pack_sdo_unit(TASK_ID_MIDLEVEL, SDO_ID_MIDLEVEL_RISK_PARAM, SDO_REQU, 3,
                               [float_to_byte_list(max_error), float_to_byte_list(max_rom),
                                float_to_byte_list(min_rom)])]
        msg = flatten_list(msg)
        self.pcan_comm.send_message(msg, SDO, self.node_id)
        
        # Position control gains
        msg = [3, pack_sdo_unit(TASK_ID_MIDLEVEL, SDO_ID_MIDLEVEL_POSITION_CTRL_P_GAIN, 
                               SDO_REQU, 1, float_to_byte_list(kp)),
               pack_sdo_unit(TASK_ID_MIDLEVEL, SDO_ID_MIDLEVEL_POSITION_CTRL_D_GAIN,
                            SDO_REQU, 1, float_to_byte_list(kd)),
               pack_sdo_unit(TASK_ID_MIDLEVEL, SDO_ID_MIDLEVEL_MID_CTRL_SATURATION,
                            SDO_REQU, 1, float_to_byte_list(sat))]
        msg = flatten_list(msg)
        self.pcan_comm.send_message(msg, SDO, self.node_id)

        # Impedance control parameters
        msg = [1, pack_sdo_unit(TASK_ID_MIDLEVEL, SDO_ID_MIDLEVEL_IMPEDANCECTRL_INFO,
                               SDO_REQU, 4,
                               [float_to_byte_list(imp_kp), float_to_byte_list(imp_kd),
                                float_to_byte_list(imp_lambda), float_to_byte_list(imp_epsilon)])]
        msg = flatten_list(msg)
        self.pcan_comm.send_message(msg, SDO, self.node_id)

    def set_walking_parameters(self, **kwargs):
        """
        걷기 모드 파라미터 설정 (키워드 기반)
        
        Parameters:
            Plantar, Dorsi, Dorsi2, T1, T2, T3, T4, T5, T6, T7, phase_shift
        
        Returns:
            (plantar_init, plantar_terminal)
        """
        plantar_amp = kwargs.get('Plantar', 5)
        dorsi_amp = kwargs.get('Dorsi', 5)
        dorsi_amp2 = kwargs.get('Dorsi2', 5)
        t1 = kwargs.get('T1', 55)
        t2 = kwargs.get('T2', 0.714)
        t3 = kwargs.get('T3', 60)
        t4 = kwargs.get('T4', 0)
        t5 = kwargs.get('T5', 0)
        t6 = kwargs.get('T6', 0)
        t7 = kwargs.get('T7', 0)
        phase_shift = kwargs.get('phase_shift', 0)
        
        plantar_init = float(format(t1 - t2 * t3, ".2f"))
        plantar_terminal = float(format(t1 + t2 * t3, ".2f"))
        
        # GUI 업데이트 (ReadOnly 라벨 업데이트)
        if self.gui_ref and hasattr(self.gui_ref, 'labels_dict'):
            labels = self.gui_ref.labels_dict
            if 'plantar_init' in labels:
                labels['plantar_init'].lineEdit.setText(str(plantar_init))
            if 'plantar_terminal' in labels:
                labels['plantar_terminal'].lineEdit.setText(str(plantar_terminal))
        
        # Ankle ref info 1
        msg = [1, pack_sdo_unit(TASK_ID_MIDLEVEL, SDO_ID_MIDLEVEL_ANKLE_REF_INFO,
                               SDO_REQU, 4,
                               [float_to_byte_list(plantar_amp), float_to_byte_list(t1),
                                float_to_byte_list(t2), float_to_byte_list(t3)])]
        msg = flatten_list(msg)
        self.pcan_comm.send_message(msg, SDO, self.node_id)

        # Ankle ref info 2
        msg = [1, pack_sdo_unit(TASK_ID_MIDLEVEL, SDO_ID_MIDLEVEL_ANKLE_REF_INFO2,
                               SDO_REQU, 4,
                               [float_to_byte_list(dorsi_amp), float_to_byte_list(dorsi_amp2),
                                float_to_byte_list(t4), float_to_byte_list(t5)])]
        msg = flatten_list(msg)
        self.pcan_comm.send_message(msg, SDO, self.node_id)

        # Ankle ref info 3
        msg = [1, pack_sdo_unit(TASK_ID_MIDLEVEL, SDO_ID_MIDLEVEL_ANKLE_REF_INFO3,
                               SDO_REQU, 2,
                               [float_to_byte_list(t6), float_to_byte_list(t7)])]
        msg = flatten_list(msg)
        self.pcan_comm.send_message(msg, SDO, self.node_id)

        # Phase shift
        msg = [1, pack_sdo_unit(TASK_ID_MIDLEVEL, SDO_ID_MIDLEVEL_PHASE_SHIFT,
                               SDO_REQU, 1, float_to_byte_list(phase_shift))]
        msg = flatten_list(msg)
        self.pcan_comm.send_message(msg, SDO, self.node_id)
        
        return plantar_init, plantar_terminal

    def set_sine_parameters(self, amp, freq):
        """
        사인파 모드 파라미터 설정
        
        Parameters:
            amp: 진폭
            freq: 주파수
        """
        msg = [1, pack_sdo_unit(TASK_ID_MIDLEVEL, SDO_ID_MIDLEVEL_POSITION_PERIODIC_SIG_INFO,
                               SDO_REQU, 3,
                               [float_to_byte_list(amp), float_to_byte_list(freq),
                                float_to_byte_list(0)])]
        msg = flatten_list(msg)
        self.pcan_comm.send_message(msg, SDO, self.node_id)

    def set_square_parameters(self, amp, a, td):
        """
        사각파(Tanh) 모드 파라미터 설정
        
        Parameters:
            amp: 진폭
            a: a 파라미터
            td: 지속시간
        """
        msg = [1, pack_sdo_unit(TASK_ID_MIDLEVEL, SDO_ID_MIDLEVEL_POSITION_TANH_INFO,
                               SDO_REQU, 3,
                               [float_to_byte_list(amp), float_to_byte_list(a),
                                float_to_byte_list(td)])]
        msg = flatten_list(msg)
        self.pcan_comm.send_message(msg, SDO, self.node_id)

    def set_periodic_ankle_parameters(self, plantar_amp, peak, ratio, width):
        """
        주기적 발목 모드 파라미터 설정
        
        Parameters:
            plantar_amp: 발바닥 진폭
            peak: 피크 시간
            ratio: 비율
            width: 너비
        """
        msg = [1, pack_sdo_unit(TASK_ID_MIDLEVEL, SDO_ID_MIDLEVEL_ANKLE_REF_INFO,
                               SDO_REQU, 4,
                               [float_to_byte_list(plantar_amp), float_to_byte_list(peak),
                                float_to_byte_list(ratio), float_to_byte_list(width)])]
        msg = flatten_list(msg)
        self.pcan_comm.send_message(msg, SDO, self.node_id)

    def set_saan_parameters(self, k_torque, max_torque, power_PF, power_DF):
        """
        SAAN 파라미터 설정
        
        Parameters:
            k_torque: K_torque (비례상수)
            max_torque: Max Torque (최대 토크)
            power_PF: Power PF (PF 지수상수)
            power_DF: Power DF (DF 지수상수)
        """
        msg = [1, pack_sdo_unit(TASK_ID_MIDLEVEL, SDO_ID_MIDLEVEL_PROPORTIONALCTRL_INFO,
                               SDO_REQU, 4,
                               [float_to_byte_list(k_torque), float_to_byte_list(max_torque),
                                float_to_byte_list(power_PF), float_to_byte_list(power_DF)])]
        msg = flatten_list(msg)
        self.pcan_comm.send_message(msg, SDO, self.node_id)

    def shift_parameters_right(self, t1=None, t2=None, t3=None, t4=None, t5=None, t6=None):
        """
        파라미터를 오른쪽으로 시프트 (값 증가)
        GUI 참조가 있으면 GUI에서 값을 읽고 업데이트
        
        Returns:
            수정된 파라미터들
        """
        # GUI에서 값을 읽어오기
        if self.gui_ref and hasattr(self.gui_ref, 'labels_dict'):
            labels = self.gui_ref.labels_dict
            try:
                t1 = float(labels.get('T1').lineEdit.text() or 0) + 1
                t2 = float(labels.get('T2').lineEdit.text() or 0) + 1
                t3 = float(labels.get('T3').lineEdit.text() or 0) + 1
                t4 = float(labels.get('T4').lineEdit.text() or 0) + 1
                t5 = float(labels.get('T5').lineEdit.text() or 0) + 1
                t6 = float(labels.get('T6').lineEdit.text() or 0) + 1
                
                # GUI 업데이트
                labels['T1'].lineEdit.setText(str(t1))
                labels['T2'].lineEdit.setText(str(t2))
                labels['T3'].lineEdit.setText(str(t3))
                labels['T4'].lineEdit.setText(str(t4))
                labels['T5'].lineEdit.setText(str(t5))
                labels['T6'].lineEdit.setText(str(t6))
            except:
                pass
        elif t1 is not None:
            return t1 + 1, t2 + 1, t3 + 1, t4 + 1, t5 + 1, t6 + 1
        
        return (t1, t2, t3, t4, t5, t6) if all([t1, t2, t3, t4, t5, t6]) else None

    def shift_parameters_left(self, t1=None, t2=None, t3=None, t4=None, t5=None, t6=None):
        """
        파라미터를 왼쪽으로 시프트 (값 감소)
        GUI 참조가 있으면 GUI에서 값을 읽고 업데이트
        
        Returns:
            수정된 파라미터들
        """
        # GUI에서 값을 읽어오기
        if self.gui_ref and hasattr(self.gui_ref, 'labels_dict'):
            labels = self.gui_ref.labels_dict
            try:
                t1 = float(labels.get('T1').lineEdit.text() or 0) - 1
                t2 = float(labels.get('T2').lineEdit.text() or 0) - 1
                t3 = float(labels.get('T3').lineEdit.text() or 0) - 1
                t4 = float(labels.get('T4').lineEdit.text() or 0) - 1
                t5 = float(labels.get('T5').lineEdit.text() or 0) - 1
                t6 = float(labels.get('T6').lineEdit.text() or 0) - 1
                
                # GUI 업데이트
                labels['T1'].lineEdit.setText(str(t1))
                labels['T2'].lineEdit.setText(str(t2))
                labels['T3'].lineEdit.setText(str(t3))
                labels['T4'].lineEdit.setText(str(t4))
                labels['T5'].lineEdit.setText(str(t5))
                labels['T6'].lineEdit.setText(str(t6))
            except:
                pass
        elif t1 is not None:
            return t1 - 1, t2 - 1, t3 - 1, t4 - 1, t5 - 1, t6 - 1
        
        return (t1, t2, t3, t4, t5, t6) if all([t1, t2, t3, t4, t5, t6]) else None
