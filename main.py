# Main loop and setup for SPS program
from time import sleep
from logger import log
from sensor import Sensor
from motor import Motor, Direction
from conveyor import Conveyor, Direction

conv1 = Conveyor(sensor_stop=None, sensor_check=Sensor("check"), motor=Motor("gear"), direction=Direction.FORWARD, max_transport_time=2)
while(True):
    conv1.update()
    if conv1.waiting_for_transport:
        log.warning("--Ready for Pickup")
        break
    elif conv1.error_no_product_found:
        log.error("No Product found")
        break

    sleep(1)
