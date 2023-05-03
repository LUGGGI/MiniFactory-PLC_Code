from revpimodio2 import RevPiModIO
from time import sleep
import atexit

def set_all_output_to_false():
    try:
        revpi = RevPiModIO(autorefresh=True)
    except:
        # load simulation if not connected to factory
        revpi = RevPiModIO(autorefresh=True, configrsc="C:/Users/LUGGGI/OneDrive - bwedu/Vorlesungen/Bachlor_Arbeit/RevPi/RevPi82247.rsc", procimg="C:/Users/LUGGGI/OneDrive - bwedu/Vorlesungen/Bachlor_Arbeit/RevPi\RevPi82247.img")
    print("Setting all outputs to false")

    list = revpi.io

    not_used_words = ["PWM", "O_", "RevPiLED", "RS485ErrorLimit"]

    for io in list:
        if io.type == 301:
            is_out = True
            for word in not_used_words:
                if str(io).find(word) != -1:
                    is_out = False
            
            if is_out:
                revpi.io[str(io)].value = False

    revpi.exit()

    sleep(1)

def exit_handler():
    atexit.register(set_all_output_to_false)


set_all_output_to_false()
# All Outputs
'''
GR3_OPEN
GR3_CLOSE
GR3_FWD
GR3_BWD
GR3_DOWN
GR3_UP
GR3_CW
GR3_CCW
VG2_UP
VG2_DOWN
VG2_BWD
VG2_FWD
VG2_CW
VG2_CCW
VG2_COMPRESSOR
VG2_VALVE_VACUUM
CB5_FWD
CB5_BWD
SL_CB_FWD
SL_COMPRESSOR
SL_VALVE_PISTON_WHITE
SL_VALVE_PISTON_RED
SL_VALVE_PISTON_BLUE
GR1_CW
GR1_CCW
GR1_DOWN
GR1_OPEN
GR1_FWD
GR1_BWD
GR1_UP
GR1_CLOSE
CB2_BWD
CB2_FWD
PM_UP
PM_CB_FWD
PM_DOWN
PM_CB_BWD
WH_CB_BWD
WH_CB_FWD
WH_ARM_FWD
WH_ARM_BWD
WH_ARM_DOWN
WH_ARM_UP
CB4_FWD
CB4_BWD
VG1_COMPRESSOR
VG1_CW
VG1_UP
VG1_VALVE_VACUUM
VG1_BWD
VG1_FWD
VG1_CCW
VG1_DOWN
CB3_FWD
CB3_BWD
GR2_BWD
GR2_CW
GR2_CCW
GR2_FWD
GR2_OPEN
GR2_UP
GR2_DOWN
GR2_CLOSE
CB1_FWD
CB1_BWD
MPS_VALVE_VG_VACUUM
MPS_VALVE_TABLE_PISTON
MPS_TABLE_CCW
MPS_LIGHT_OVEN
MPS_CB_FWD
MPS_COMPRESSOR
MPS_TABLE_CW
MPS_OVEN_TRAY_OUT
MPS_SAW
MPS_VALVE_VG_LOWER
MPS_VALVE_OVEN_DOOR
MPS_OVEN_TRAY_IN'''