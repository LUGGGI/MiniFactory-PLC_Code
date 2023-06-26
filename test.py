


class Test:
    def __init__(self) -> None:
        self.dic = {}
        self.liste: list = []
        self.value: int = None

a = Test()
b = Test()

a.dic["a"] = "a"
a.liste = ["a"]
a.value = 1

print(f"b= {b.dic}, {b.liste}, {b.value}")
