import threading
from time import sleep

class Test():
    stop = False
    a = {}
    line_config = {
        "name": "Main1", 
        "run": True,
        "start_at": "start",
        "end_at": "END",
        "with_oven": True,
        "with_saw": True,
        "with_PM": False,
        "with_WH": False,
        "color": "WHITE"
    }
    factory_config = {
        "exit_if_end": True
    }

    def read(self):
        while True:
            if self.stop:
                return
            if self.a == self.line_config or self.a == self.factory_config:
                continue
            else:
                print(self.a)

    def write(self):
        while True:
            if self.stop:
                return
            self.a = self.line_config
            self.a = self.factory_config

test = Test()
t1 = threading.Thread(target=test.read)
t2 = threading.Thread(target=test.write)

t1.start()
t2.start()

sleep(3)
test.stop = True