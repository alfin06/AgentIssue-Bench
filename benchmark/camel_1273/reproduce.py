# from camel.utils import api_keys_required

# class DummyClass:
#     @api_keys_required([("DUMMY_TOKEN", "DUMMY_TOKEN")])
#     def __init__(self, api_key: str):
#         self._api_key = api_key

# dc = DummyClass(api_key="xxxxx")


from camel.utils import api_keys_required


class DummyClass:
    @api_keys_required("DUMMY_TOKEN")
    def __init__(self, api_key: str):
        self._api_key = api_key


dc = DummyClass(api_key="xxxxx")