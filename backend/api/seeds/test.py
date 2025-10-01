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


"""
def list_mapping(self, *, exchange_id: int | None = None) -> list[ExchangeInstrumentModel]:
        ei = ExchangeInstrumentModel

        stmt = select(ei.exchange_id, ei.base_asset_id, ei.quote_asset_id)
        if exchange_id:
            stmt = stmt.where(ei.exchange_id == exchange_id)
        
        rows = self._db.execute(stmt).scalars().all() [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        rows = self._db.execute(stmt).tuples().all() [(1, 101, 202), (1, 102, 202), (1, 103, 202), (1, 104, 202), (1, 105, 202), (1, 106, 202), (1, 107, 202), (1, 108, 202), (1, 109, 202), (1, 110, 202)]
        rows = self._db.execute(stmt).mappings().all() 
        [{'exchange_id': 1, 'base_asset_id': 101, 'quote_asset_id': 202}, {'exchange_id': 1, 'base_asset_id': 102, 'quote_asset_id': 202}, {'exchange_id': 1, 'base_asset_id': 103, 'quote_asset_id': 202}, {'exchange_id': 1, 'base_asset_id': 104, 'quote_asset_id': 202}, {'exchange_id': 1, 'base_asset_id': 105, 'quote_asset_id': 202}, {'exchange_id': 1, 'base_asset_id': 106, 'quote_asset_id': 202}, {'exchange_id': 1, 'base_asset_id': 107, 'quote_asset_id': 202}, {'exchange_id': 1, 'base_asset_id': 108, 'quote_asset_id': 202}, {'exchange_id': 1, 'base_asset_id': 109, 'quote_asset_id': 202}, {'exchange_id': 1, 'base_asset_id': 110, 'quote_asset_id': 202}]

"""