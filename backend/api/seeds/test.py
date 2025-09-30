from typing import Literal
Interval = Literal["1m","5m","15m","1h","4h","1d","1w","1M"]

def _floor(out: Interval):
    print(out)

_floor()

# class TestA():
#     A = 1

#     def test_a_func():
#         B = 2
#         return B

# def test_a(model):
#     print(model.A)


# test_a(TestA)
# print(TestA.test_a_func)
# print(TestA.test_a_func())


# print("--------------------")

# class TestB():
#     A = 1

#     def test_b_func(self):
#         B = 2
#         return B

# def test_b(model):
#     print(model.A)


# test_b(TestB)
# cls_b = TestB()
# print(cls_b.test_b_func())
# print(TestB.test_b_func())


# label = "15m"

# if label.endswith("m"): print(label[:-1])


