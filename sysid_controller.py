"""
System Identification controller module
"""

from constants import *
from message_handler import pack_sdo_unit, flatten_list, float_to_byte_list


class SystemIDController:
    """System Identification control class"""
    
    def __init__(self, pcan_communicator, node_id=0x07):
        """
        Initialize
        
        Parameters:
            pcan_communicator: PCAN communicator object
            node_id: Node ID
        """
        self.pcan_comm = pcan_communicator
        self.node_id = node_id
        self.sysid_done = 0

    def _send_message(self, msg):
        """Send message"""
        msg = flatten_list(msg)
        return self.pcan_comm.send_message(msg, SDO, self.node_id)

    def apply_settings(self, min_freq, max_freq, n_sample, n_iter, mag, offset):
        """
        Apply System ID settings
        
        Parameters:
            min_freq: Minimum frequency
            max_freq: Maximum frequency
            n_sample: Number of samples
            n_iter: Number of iterations
            mag: Input magnitude
            offset: Input offset
        """
        msg = [1, pack_sdo_unit(TASK_ID_MIDLEVEL, SDO_ID_MIDLEVEL_SYSTEM_ID_SBS_INFO, SDO_REQU, 6, 
                               [float_to_byte_list(min_freq), float_to_byte_list(max_freq), 
                                float_to_byte_list(n_sample), float_to_byte_list(n_iter), 
                                float_to_byte_list(mag), float_to_byte_list(offset)])]
        msg = flatten_list(msg)
        self.pcan_comm.send_message(msg, SDO, self.node_id)

    def start(self):
        """Start System ID"""
        self.sysid_done = 1
        
        # Message 1: Set state and PDO list
        pdo_list = [TASK_ID_MIDLEVEL, PDO_ID_MIDLEVEL_VELOCITY_ESTIMATED,
                   TASK_ID_MIDLEVEL, PDO_ID_MIDLEVEL_SYSTEM_ID_SBS_FREQ,
                   TASK_ID_LOWLEVEL, PDO_ID_LOWLEVEL_CURRENT_OUTPUT,
                   TASK_ID_MIDLEVEL, PDO_ID_MIDLEVEL_LOOP_CNT,
                   TASK_ID_MIDLEVEL, PDO_ID_MIDLEVEL_REF_VELOCITY,
                   TASK_ID_MIDLEVEL, PDO_ID_MIDLEVEL_LOADCELL_FORCE,
                   TASK_ID_MIDLEVEL, PDO_ID_MIDLEVEL_SBS_ID_DONE]
        
        msg = [4, pack_sdo_unit(TASK_ID_MSG, SDO_ID_MSG_SET_STATE, SDO_REQU, 1, STATE_STANDBY),
               TASK_ID_MSG, SDO_ID_MSG_PDO_LIST, SDO_REQU, 7] + pdo_list + \
              [pack_sdo_unit(TASK_ID_MSG, SDO_ID_MSG_GUI_COMM_ONOFF, SDO_REQU, 1, 0),
               pack_sdo_unit(TASK_ID_MSG, SDO_ID_MSG_GUI_COMM_COMMAND, SDO_REQU, 1, MECH_SYS_ID_SBS_RAW_DATA)]
        msg = flatten_list(msg)
        self.pcan_comm.send_message(msg, SDO, self.node_id)

        # Message 2: Set routines
        msg = [3, pack_sdo_unit(TASK_ID_MSG, SDO_ID_MSG_SET_ROUTINE, SDO_REQU, 1, ROUTINE_ID_MSG_PDO_SEND),
               pack_sdo_unit(TASK_ID_LOWLEVEL, SDO_ID_LOWLEVEL_SET_ROUTINE, SDO_REQU, 1, ROUTINE_ID_LOWLEVEL_CURRENT_CTRL),
               pack_sdo_unit(TASK_ID_MIDLEVEL, SDO_ID_MIDLEVEL_SET_ROUTINE, SDO_REQU, 2, 
                            [ROUTINE_ID_MIDLEVEL_VELOCITY_CTRL, ROUTINE_ID_MIDLEVEL_SYS_ID_SBS])]
        msg = flatten_list(msg)
        self.pcan_comm.send_message(msg, SDO, self.node_id)

        # Message 3: Set state to Enable
        msg = [3, pack_sdo_unit(TASK_ID_LOWLEVEL, SDO_ID_LOWLEVEL_SET_STATE, SDO_REQU, 1, STATE_ENABLE),
               pack_sdo_unit(TASK_ID_MIDLEVEL, SDO_ID_MIDLEVEL_SET_STATE, SDO_REQU, 1, STATE_ENABLE),
               pack_sdo_unit(TASK_ID_MSG, SDO_ID_MSG_SET_STATE, SDO_REQU, 1, STATE_ENABLE)]
        msg = flatten_list(msg)
        self.pcan_comm.send_message(msg, SDO, self.node_id)

    def stop(self):
        """Stop System ID"""
        self.sysid_done = 0
        
        msg = [3, pack_sdo_unit(TASK_ID_LOWLEVEL, SDO_ID_LOWLEVEL_SET_STATE, SDO_REQU, 1, STATE_STANDBY),
               pack_sdo_unit(TASK_ID_MIDLEVEL, SDO_ID_MIDLEVEL_SET_STATE, SDO_REQU, 1, STATE_STANDBY),
               pack_sdo_unit(TASK_ID_MSG, SDO_ID_MSG_SET_STATE, SDO_REQU, 1, STATE_STANDBY)]
        msg = flatten_list(msg)
        self.pcan_comm.send_message(msg, SDO, self.node_id)
