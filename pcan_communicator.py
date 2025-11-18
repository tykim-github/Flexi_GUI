"""
PCAN 통신 관련 기능들
"""

from PCANBasic import *
from message_handler import get_dlc_from_length
import struct


class PCANCommunicator:
    """PCAN 통신 처리 클래스"""
    
    def __init__(self, pcan_handle=PCAN_USBBUS1, is_fd=True, 
                 bitrate=PCAN_BAUD_1M, 
                 bitrate_fd=b'f_clock_mhz=80,nom_brp=10,nom_tseg1=5,nom_tseg2=2,nom_sjw=2,data_brp=1,data_tseg1=11,data_tseg2=4,data_sjw=4'):
        """
        PCAN 통신 초기화
        
        Parameters:
            pcan_handle: PCAN 채널 핸들
            is_fd: FD 모드 사용 여부
            bitrate: 비트율 (non-FD)
            bitrate_fd: FD 비트율 설정
        """
        self.pcan_handle = pcan_handle
        self.is_fd = is_fd
        self.bitrate = bitrate
        self.bitrate_fd = bitrate_fd
        self.obj_pcan_basic = None
        self.dll_found = False
        
    def initialize(self):
        """
        PCAN 초기화
        
        Returns:
            성공 여부
        """
        try:
            self.obj_pcan_basic = PCANBasic()
            self.dll_found = True
        except:
            print("Unable to find the library: PCANBasic.dll !")
            self.dll_found = False
            return False

        # Initialize the selected channel
        if self.is_fd:
            sts_result = self.obj_pcan_basic.InitializeFD(self.pcan_handle, self.bitrate_fd)
        else:
            sts_result = self.obj_pcan_basic.Initialize(self.pcan_handle, self.bitrate)
            
        if sts_result != PCAN_ERROR_OK:
            print("Can not initialize. Please check the defines in the code.")
            self.show_status(sts_result)
            return False

        print("Successfully initialized.")
        return True

    def send_message(self, msg_data, sdo, node_id):
        """
        CAN 메시지 전송
        
        Parameters:
            msg_data: 메시지 데이터
            sdo: SDO/PDO 타입
            node_id: 노드 ID
            
        Returns:
            전송 결과
        """
        # PCAN이 초기화되지 않았으면 실패
        if self.obj_pcan_basic is None:
            print("PCAN not initialized. Call initialize() first.")
            return False
        
        msg_can_message_fd = TPCANMsgFD()
        msg_can_message_fd.ID = sdo | (1 << 4) | node_id
        msg_len = len(msg_data)
        msg_can_message_fd.DLC = get_dlc_from_length(msg_len)
        msg_can_message_fd.MSGTYPE = PCAN_MESSAGE_FD.value | PCAN_MESSAGE_BRS.value
        
        for i in range(msg_len):
            msg_can_message_fd.DATA[i] = msg_data[i]
            
        return self.obj_pcan_basic.WriteFD(self.pcan_handle, msg_can_message_fd)

    def read_message(self):
        """
        CAN 메시지 수신
        
        Returns:
            (상태, 메시지)
        """
        if self.is_fd:
            return self.obj_pcan_basic.ReadFD(self.pcan_handle)
        else:
            return self.obj_pcan_basic.Read(self.pcan_handle)

    def read_all_messages(self):
        """
        큐의 모든 메시지를 읽기
        
        Returns:
            메시지 리스트
        """
        messages = []
        sts_result = [PCAN_ERROR_OK]
        
        while sts_result[0] != PCAN_ERROR_QRCVEMPTY:
            sts_result = self.read_message()
            
            if sts_result[0] != PCAN_ERROR_OK and sts_result[0] != PCAN_ERROR_QRCVEMPTY:
                self.show_status(sts_result[0])
                break
                
            if sts_result[0] == PCAN_ERROR_OK:
                messages.append(sts_result[1])
                
        return messages

    def show_status(self, status):
        """
        상태 메시지 표시
        
        Parameters:
            status: 상태 코드
        """
        print("=" * 90)
        print(self.get_formatted_error(status))
        print("=" * 90)

    def get_formatted_error(self, error):
        """
        에러 코드를 텍스트로 변환
        
        Parameters:
            error: 에러 코드
            
        Returns:
            에러 메시지 텍스트
        """
        sts_return = self.obj_pcan_basic.GetErrorText(error, 0x09)
        if sts_return[0] != PCAN_ERROR_OK:
            return "An error occurred. Error-code's text ({0:X}h) couldn't be retrieved".format(error)
        else:
            message = str(sts_return[1])
            return message.replace("'", "", 2).replace("b", "", 1)

    def uninitialize(self):
        """
        PCAN 종료
        """
        if self.dll_found and self.obj_pcan_basic:
            self.obj_pcan_basic.Uninitialize(PCAN_NONEBUS)

    def configure_trace(self, trace_path=b'', trace_size=100, trace_single=True, 
                       trace_date=True, trace_time=True, trace_overwrite=False, 
                       trace_data_length=False):
        """
        트레이스 파일 설정
        
        Parameters:
            trace_path: 저장 경로
            trace_size: 파일 크기 (MB)
            trace_single: 단일 파일 여부
            trace_date: 날짜 추가 여부
            trace_time: 시간 추가 여부
            trace_overwrite: 덮어쓰기 여부
            trace_data_length: Data Length 사용 여부
            
        Returns:
            성공 여부
        """
        sts_result = self.obj_pcan_basic.SetValue(self.pcan_handle, PCAN_TRACE_LOCATION, trace_path)
        
        if sts_result == PCAN_ERROR_OK:
            sts_result = self.obj_pcan_basic.SetValue(self.pcan_handle, PCAN_TRACE_SIZE, trace_size)
            
            if sts_result == PCAN_ERROR_OK:
                if trace_single:
                    config = TRACE_FILE_SINGLE
                else:
                    config = TRACE_FILE_SEGMENTED

                if trace_overwrite:
                    config = config | TRACE_FILE_OVERWRITE

                if trace_data_length:
                    config = config | TRACE_FILE_DATA_LENGTH
                
                if trace_date:
                    config = config | TRACE_FILE_DATE

                if trace_time:
                    config = config | TRACE_FILE_TIME

                sts_result = self.obj_pcan_basic.SetValue(self.pcan_handle, PCAN_TRACE_CONFIGURE, config)
                
                if sts_result == PCAN_ERROR_OK:
                    return True
                    
        self.show_status(sts_result)
        return False

    def start_trace(self):
        """
        트레이싱 시작
        
        Returns:
            성공 여부
        """
        sts_result = self.obj_pcan_basic.SetValue(self.pcan_handle, PCAN_TRACE_STATUS, PCAN_PARAMETER_ON)
        
        if sts_result != PCAN_ERROR_OK:
            self.show_status(sts_result)
            return False
            
        return True

    def stop_trace(self):
        """
        트레이싱 중지
        
        Returns:
            성공 여부
        """
        sts_result = self.obj_pcan_basic.SetValue(self.pcan_handle, PCAN_TRACE_STATUS, PCAN_PARAMETER_OFF)
        
        if sts_result != PCAN_ERROR_OK:
            self.show_status(sts_result)
            return False
            
        return True
