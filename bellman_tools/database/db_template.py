class db_template():
    __tablename__ = 'DB_Template'

    def __repr__(self):
        return vars(self).__str__()

    def to_dict(self):
        dic = vars(self)
        res = dic.copy()
        if '_sa_instance_state' in res: res.pop('_sa_instance_state')
        return res

    def is_empty(self):
        for key, value in self.to_dict().items():
            if value is not None: return False
        return True

    def get_attributes_unloaded_to_dict(self):
        res = {}
        for attr in self.__dict__['_sa_instance_state'].unloaded:
            res[attr] = None
        return res

    def get_all_atributes_to_dic(self):
        attr_loaded = self.to_dict()
        attr_unloaded = self.get_attributes_unloaded_to_dict()
        res = {**attr_loaded, **attr_unloaded}
        return res

    def generate_select_sql_query(self, table_name):

        dict = self.get_all_atributes_to_dic()
        dict.pop('ID', None)
        res = "SELECT {fields} FROM {table}".format(
            fields=', '.join(dict.keys()), table=table_name
        )
        return res


if __name__ == '__main__':
    pass
