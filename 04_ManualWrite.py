## Needed Imports
from PCANBasic import *
import os
import sys
import struct

class ManualWrite():

    # Defines
    #region

    # Sets the PCANHandle (Hardware Channel)
    PcanHandle = PCAN_USBBUS2

    # Sets the desired connection mode (CAN = false / CAN-FD = true)
    IsFD = True

    # Sets the bitrate for normal CAN devices
    Bitrate = PCAN_BAUD_500K

    # Sets the bitrate for CAN FD devices. 
    # Example - Bitrate Nom: 1Mbit/s Data: 2Mbit/s:
    #   "f_clock_mhz=20, nom_brp=5, nom_tseg1=2, nom_tseg2=1, nom_sjw=1, data_brp=2, data_tseg1=3, data_tseg2=1, data_sjw=1"
    BitrateFD = b'f_clock_mhz=80,nom_brp=1,nom_tseg1=127,nom_tseg2=32,nom_sjw=32,data_brp=1,data_tseg1=11,data_tseg2=4,data_sjw=4'
    #endregion

    # Members
    #region

    # Shows if DLL was found
    m_DLLFound = False
    ## STATE
    State_Off     = 0
    State_Standby = 1
    State_Enable  = 2
    State_Error   = 3
    #endregion\
    node_id=0x06
    # MSG FNC CODE
    EMCY = 0x000
    SYNC = 0x100
    SDO = 0x200
    PDO = 0x300
    TIMEOUT = 0x400
    GUI_SYNC = 0x500

    # MSG FNC CODE
    EMCY_SEND = 0x00
    SYNC_SEND = 0x01
    SDO_SEND = 0x02
    PDO_SEND = 0x03
    TIMEOUT_SEND = 0x04
    GUI_SYNC_SEND = 0x05

    # Node ID
    NODE_ID_ALL = 0x00
    NODE_ID_CM = 0x10
    NODE_ID_LH = 0x20
    NODE_ID_RH = 0x30
    NODE_ID_LK = 0x40
    NODE_ID_RK = 0x50
    NODE_ID_LA = 0x60
    NODE_ID_RA = 0x70

    # TASK ID
    TASK_ID_LOWLEVEL = 0x00
    TASK_ID_MIDLEVEL = 0x01
    TASK_ID_MSG = 0x02
    TASK_ID_IMU = 0x03
    TASK_ID_SYSMNGT = 0x04
    TASK_ID_EXTDEV = 0x05

    # SDO FNC
    SDO_IDLE  =2
    SDO_REQU  =1
    SDO_SUCC  =0
    SDO_FAIL =255

    SDO_ID_MIDLEVEL_GET_STATE                    =0x00
    SDO_ID_MIDLEVEL_SET_STATE                    =0x01
    SDO_ID_MIDLEVEL_GET_ROUTINE                  =0x02
    SDO_ID_MIDLEVEL_SET_ROUTINE                  =0x03
    SDO_ID_MIDLEVEL_MID_CTRL_SATURATION          =0x1A
    def __init__(self):
        """
        Create an object starts the programm
        """
        self.ShowConfigurationHelp() ## Shows information about this sample
        self.ShowCurrentConfiguration() ## Shows the current parameters configuration

        ## Checks if PCANBasic.dll is available, if not, the program terminates
        try:
            self.m_objPCANBasic = PCANBasic()
            self.m_DLLFound = True
        except :
            print("Unable to find the library: PCANBasic.dll !")
            self.getInput("Press <Enter> to quit...")
            self.m_DLLFound = False
            return

        
        ## Initialization of the selected channel
        if self.IsFD:
            stsResult = self.m_objPCANBasic.InitializeFD(self.PcanHandle,self.BitrateFD)
        else:
            stsResult = self.m_objPCANBasic.Initialize(self.PcanHandle,self.Bitrate)

        if stsResult != PCAN_ERROR_OK:
            print("Can not initialize. Please check the defines in the code.")
            self.ShowStatus(stsResult)
            print("")
            self.getInput("Press <Enter> to quit...")
            return

        ## Writing messages...
        print("Successfully initialized.")
        self.getInput("Press <Enter> to write...")
        strinput = "y"
        while strinput == "y":
            self.clear()
            self.WriteMessages()
            strinput = self.getInput("Do you want to write again? yes[y] or any other key to exit...", "y")
            strinput = chr(ord(strinput))

    def __del__(self):
        if self.m_DLLFound:
            self.m_objPCANBasic.Uninitialize(PCAN_NONEBUS)

    def getInput(self, msg="Press <Enter> to continue...", default=""):
        res = default
        if sys.version_info[0] >= 3:
            res = input(msg + " ")
        else:
            res = raw_input(msg + " ")
        if len(res) == 0:
            res = default
        return res

    # Main-Functions
    #region
    def WriteMessages(self):
        '''
        Function for writing PCAN-Basic messages
        '''
        if self.IsFD:
            stsResult = self.WriteMessageFD()
        else:
            stsResult = self.WriteMessage()

        ## Checks if the message was sent
        if (stsResult != PCAN_ERROR_OK):
            self.ShowStatus(stsResult)
        else:
            print("Message was successfully SENT")

    def WriteMessage(self):
        """
        Function for writing messages on CAN devices

        Returns:
            A TPCANStatus error code
        """
        ## Sends a CAN message with extended ID, and 8 data bytes
        msgCanMessage = TPCANMsg()
        msgCanMessage.ID = 0x100
        msgCanMessage.LEN = 8
        msgCanMessage.MSGTYPE = PCAN_MESSAGE_EXTENDED.value
        for i in range(8):
            msgCanMessage.DATA[i] = i
            pass
        return self.m_objPCANBasic.Write(self.PcanHandle, msgCanMessage)

    def WriteMessageFD(self):
        """
        Function for writing messages on CAN-FD devices

        Returns:
            A TPCANStatus error code
        """
        ## Sends a CAN-FD message with standard ID, 64 data bytes, and bitrate switch
        msgCanMessageFD = TPCANMsgFD()
        send_msg=[2, self.pack_sdoUnit(self.TASK_ID_MIDLEVEL, self.SDO_ID_MIDLEVEL_SET_STATE, self.SDO_REQU, 1,
         self.State_Enable), 
                  self.pack_sdoUnit(self.TASK_ID_MIDLEVEL, self.SDO_ID_MIDLEVEL_MID_CTRL_SATURATION, self.SDO_REQU, 1, [self.float_to_byte_list(2.5),self.float_to_byte_list(2.5)])]
        send_msg = self.flatten_list(send_msg)
        msg_len=len(send_msg)
        print(f"msg_lin is {msg_len}")
        print(send_msg)
        msgCanMessageFD.ID = self.SDO|1<<4|self.node_id
        msgCanMessageFD.DLC = self.GetDLCFromlength(msg_len)
        msgCanMessageFD.MSGTYPE = PCAN_MESSAGE_FD.value | PCAN_MESSAGE_BRS.value
        for i in range(msg_len):
            print(i)
            msgCanMessageFD.DATA[i]=send_msg[i]
            pass
        return self.m_objPCANBasic.WriteFD(self.PcanHandle, msgCanMessageFD)
    #endregion
    def flatten_list(self, nested_list):
        flat_list = []
        for item in nested_list:
            if isinstance(item, list):
                flat_list.extend(self.flatten_list(item))
            else:
                flat_list.append(item)
        return flat_list
    def float_to_byte_list(self, value):
        # 'f'는 싱글 프리시전 플로트를 나타내며, '!'는 네트워크 (=빅 엔디언) 바이트 순서를 사용함을 의미합니다.
        packed_float = struct.pack('f', value)
        # 바이트 데이터를 리스트로 변환
        byte_list = list(packed_float)
        return byte_list
    def pack_sdoUnit(self,task_id, sdo_id, status, length, value):
        # Start with the initial part of the message
        temp = [task_id, sdo_id, status, length]
        
        # Append additional bytes based on the 'value' list
        if length==1:
            temp.extend([value])
        else:
            for i in range(length):
                # Assuming value[i] is already an integer and fits into uint8
                temp.extend(struct.pack('B', value[i]))
        return temp
    def GetDLCFromlength(self, length):
        """
        Gets the data length of a CAN message

        Parameters:
            dlc = Data length code of a CAN message

        Returns:
            Data length as integer represented by the given DLC code
        """
        if length<=12:
            return 9
        elif length<=16:
            return 10
        elif length<=20:
            return 11
        elif length<=24:
            return 12
        elif length<=32:
            return 13
        elif length<=48:
            return 14
        elif length<=64:
            return 15

    # Help-Functions
    #region
    def clear(self):
        """
        Clears the console
        """
        if os.name=='nt':
            os.system('cls')
        else:
            os.system('clear')
        
    def ShowConfigurationHelp(self):
        """
        Shows/prints the configurable parameters for this sample and information about them
        """
        print("=========================================================================================")
        print("|                        PCAN-Basic ManualWrite Example                                  |")
        print("=========================================================================================")
        print("Following parameters are to be adjusted before launching, according to the hardware used |")
        print("                                                                                         |")
        print("* PcanHandle: Numeric value that represents the handle of the PCAN-Basic channel to use. |")
        print("              See 'PCAN-Handle Definitions' within the documentation                     |")
        print("* IsFD: Boolean value that indicates the communication mode, CAN (false) or CAN-FD (true)|")
        print("* Bitrate: Numeric value that represents the BTR0/BR1 bitrate value to be used for CAN   |")
        print("           communication                                                                 |")
        print("* BitrateFD: String value that represents the nominal/data bitrate value to be used for  |")
        print("             CAN-FD communication                                                        |")
        print("=========================================================================================")
        print("")

    def ShowCurrentConfiguration(self):
        """
        Shows/prints the configured paramters
        """
        print("Parameter values used")
        print("----------------------")
        print("* PCANHandle: " + self.FormatChannelName(self.PcanHandle))
        print("* IsFD: " + str(self.IsFD))
        print("* Bitrate: " + self.ConvertBitrateToString(self.Bitrate))
        print("* BitrateFD: " + self.ConvertBytesToString(self.BitrateFD))
        print("")

    def ShowStatus(self,status):
        """
        Shows formatted status

        Parameters:
            status = Will be formatted
        """
        print("=========================================================================================")
        print(self.GetFormattedError(status))
        print("=========================================================================================")
    
    def FormatChannelName(self, handle, isFD=False):
        """
        Gets the formated text for a PCAN-Basic channel handle

        Parameters:
            handle = PCAN-Basic Handle to format
            isFD = If the channel is FD capable

        Returns:
            The formatted text for a channel
        """
        handleValue = handle.value
        if handleValue < 0x100:
            devDevice = TPCANDevice(handleValue >> 4)
            byChannel = handleValue & 0xF
        else:
            devDevice = TPCANDevice(handleValue >> 8)
            byChannel = handleValue & 0xFF

        if isFD:
           return ('%s:FD %s (%.2Xh)' % (self.GetDeviceName(devDevice.value), byChannel, handleValue))
        else:
           return ('%s %s (%.2Xh)' % (self.GetDeviceName(devDevice.value), byChannel, handleValue))

    def GetFormattedError(self, error):
        """
        Help Function used to get an error as text

        Parameters:
            error = Error code to be translated

        Returns:
            A text with the translated error
        """
        ## Gets the text using the GetErrorText API function. If the function success, the translated error is returned.
        ## If it fails, a text describing the current error is returned.
        stsReturn = self.m_objPCANBasic.GetErrorText(error,0x09)
        if stsReturn[0] != PCAN_ERROR_OK:
            return "An error occurred. Error-code's text ({0:X}h) couldn't be retrieved".format(error)
        else:
            message = str(stsReturn[1])
            return message.replace("'","",2).replace("b","",1)

    def GetDeviceName(self, handle):
        """
        Gets the name of a PCAN device

        Parameters:
            handle = PCAN-Basic Handle for getting the name

        Returns:
            The name of the handle
        """
        switcher = {
            PCAN_NONEBUS.value: "PCAN_NONEBUS",
            PCAN_PEAKCAN.value: "PCAN_PEAKCAN",
            PCAN_DNG.value: "PCAN_DNG",
            PCAN_PCI.value: "PCAN_PCI",
            PCAN_USB.value: "PCAN_USB",
            PCAN_VIRTUAL.value: "PCAN_VIRTUAL",
            PCAN_LAN.value: "PCAN_LAN"
        }

        return switcher.get(handle,"UNKNOWN")   

    def ConvertBitrateToString(self, bitrate):
        """
        Convert bitrate c_short value to readable string

        Parameters:
            bitrate = Bitrate to be converted

        Returns:
            A text with the converted bitrate
        """
        m_BAUDRATES = {PCAN_BAUD_1M.value:'1 MBit/sec', PCAN_BAUD_800K.value:'800 kBit/sec', PCAN_BAUD_500K.value:'500 kBit/sec', PCAN_BAUD_250K.value:'250 kBit/sec',
                       PCAN_BAUD_125K.value:'125 kBit/sec', PCAN_BAUD_100K.value:'100 kBit/sec', PCAN_BAUD_95K.value:'95,238 kBit/sec', PCAN_BAUD_83K.value:'83,333 kBit/sec',
                       PCAN_BAUD_50K.value:'50 kBit/sec', PCAN_BAUD_47K.value:'47,619 kBit/sec', PCAN_BAUD_33K.value:'33,333 kBit/sec', PCAN_BAUD_20K.value:'20 kBit/sec',
                       PCAN_BAUD_10K.value:'10 kBit/sec', PCAN_BAUD_5K.value:'5 kBit/sec'}
        return m_BAUDRATES[bitrate.value]

    def ConvertBytesToString(self, bytes):
        """
        Convert bytes value to string

        Parameters:
            bytes = Bytes to be converted

        Returns:
            Converted bytes value as string
        """
        return str(bytes).replace("'","",2).replace("b","",1)
    #endregion

## Starts the program
ManualWrite()