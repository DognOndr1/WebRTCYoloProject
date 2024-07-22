class ikisayi(object):

    def __init__(self, a, b):
        self.a = a
        self.b = b

    @classmethod
    def toplam(self):
        return self.a + self.b


x = ikisayi(3, 5)
print("first: ", x.toplam)
print("second: ", ikisayi.toplam)
print("third: ", x.toplam())
print("fourth: ", ikisayi.toplam(x))
