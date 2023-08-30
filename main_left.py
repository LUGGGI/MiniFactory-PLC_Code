'''
Main Loop for left MiniFactory project for machines:
Conveyor
PunchMach
Warehouse
VacRobot
GripRobot
SortLine
MPStation

#dicitonary with Gripper1 Values
gr1_dict = {
    'revpickup_rotation' : 1950, #safe
    'revpickup_vertical': 3500, #safe
    'revpickup_horizontal' : 75, #safe
    'revhandover_rotation' : 870, #safe
    'revhandover_vertical' : 1000, #safe   
    'revhandover_horizontal' : 65, #safe
    'gripper_close' : 12 #safe
            }
#----------------------------------------------------------------------------------------------------
#dicitonary with Gripper2 Values
gr2_dict = {
    'revpickup_rotation' : 340, #safe
    'revpickup_vertical': 2400, #safe
    'revpickup_horizontal' : 75, #safe
    'revhandover_rotation' : 3675, #safe
    'revhandover_vertical' : 1950, #safe
    'revhandover_horizontal' : 72, #safe
    'gripper_close' : 12 #safe
            }
#----------------------------------------------------------------------------------------------------
#dicitonary with Gripper3 Values
gr3_dict = {
    'revpickup_rotation' : 1950, #safe
    'revpickup_vertical': 2000, #safe
    'revpickup_horizontal' : 30, #safe
    'revhandover_rotation' : 100, #safe
    'revhandover_vertical' : 3500, #safe   
    'revhandover_horizontal' : 75, #safe
    'gripper_close' : 12 #safe
            }
#----------------------------------------------------------------------------------------------------
#dicitonary with Gripper4 Values - virtuell, for Transport from Punching machine to Convoyer - not verified
gr4_dict = {
    'revpickup_rotation' : 3665, #safe
    'revpickup_vertical': 2000, #safe
    'revpickup_horizontal' : 75, #safe
    'revhandover_rotation' : 1960, #safe
    'revhandover_vertical' : 2500, #safe
    'revhandover_horizontal' : 1, #safe
    'gripper_close' : 12 #safe
            }

vg_dict = {
    'revconvoyer_rotation' : 915, 
    'revconvoyer_vertical': 1380, 
    'revconvoyer_horizontal' : 1950, 
    'revwarehouse_rotation' : 2720, 
    'revwarehouse_vertical' : 500,    
    'revwarehouse_horizontal' : 1460,
    'travel_rotation' : 1800,
    'travel_horizontal' : 1000,
    'travel_vertical': 110
}

'''