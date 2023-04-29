import revpimodio2
from time import sleep

rpi = revpimodio2.RevPiModIO(autorefresh=True, configrsc="C:/Users/LUGGGI/OneDrive - bwedu/Vorlesungen/Bachlor_Arbeit/RevPi/RevPi82247.rsc", procimg="C:/Users/LUGGGI/OneDrive - bwedu/Vorlesungen/Bachlor_Arbeit/RevPi\RevPi82247.img")

print("start")
# rpi.io["CB2_FWD"].value = True

# for i in range(10):
#     print(rpi.io["CB2_SENS_END"].value)
#     sleep(1)
def event_product_detected(io_name, io_value):
    print("event")
    

rpi.io["CB2_SENS_END"].reg_event(event_product_detected, edge=revpimodio2.BOTH) 
rpi.mainloop(blocking=False)
# rpi.io["CB2_FWD"].value = False
print("test")




sleep(10)
rpi.exit()



sleep(0.1)