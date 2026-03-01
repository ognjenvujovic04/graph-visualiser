class JsonConfig(object):
    def __init__(self, id_key: str = "@id", ref_key: str = "@ref", treat_string_refs_as_ids: bool = True):
        self.__id_key = None
        self.__ref_key = None
        self.__treat_string_refs_as_ids = None

        self.id_key = id_key
        self.ref_key = ref_key
        self.treat_string_refs_as_ids = treat_string_refs_as_ids

    @property
    def id_key(self):
        return self.__id_key

    @id_key.setter
    def id_key(self, value: str):
        if isinstance(value, str) and value.strip() != "":
            self.__id_key = value
        else:
            raise TypeError("id_key must be non-empty str")

    @property
    def ref_key(self):
        return self.__ref_key

    @ref_key.setter
    def ref_key(self, value: str):
        if isinstance(value, str) and value.strip() != "":
            self.__ref_key = value
        else:
            raise TypeError("ref_key must be non-empty str")

    @property
    def treat_string_refs_as_ids(self):
        return self.__treat_string_refs_as_ids

    @treat_string_refs_as_ids.setter
    def treat_string_refs_as_ids(self, value: bool):
        if isinstance(value, bool):
            self.__treat_string_refs_as_ids = value
        else:
            raise TypeError("treat_string_refs_as_ids must be bool")