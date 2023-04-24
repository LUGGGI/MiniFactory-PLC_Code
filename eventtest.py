import revpimodio2
from time import sleep

rpi = revpimodio2.RevPiModIO(autorefresh=True)

rpi.io["CB2_MOTOR_FWD"].value = True
# sleep(1)

# for i in range(10):
#     print(rpi.io.CB2_LIGHT_LEFT.value)
#     sleep(1)
result = rpi.io["CB2_LIGHT_LEFT"].wait(edge=revpimodio2.FALLING, exitevent=None, okvalue=None, timeout=10000) 

rpi.io["CB2_MOTOR_FWD"].value = False
print(result)









sleep(1)