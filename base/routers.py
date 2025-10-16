class DataDiriRouter:
    """
    Router untuk menyimpan semua DataDiri ke database 'datadiriall'.
    """
    route_app_labels = {'base'}  # ganti sesuai nama app-mu

    def db_for_read(self, model, **hints):
        if model.__name__ == 'DataDiri':
            return 'datadiriall'
        return None

    def db_for_write(self, model, **hints):
        if model.__name__ == 'DataDiri':
            return 'datadiriall'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        # Membolehkan relasi di semua database
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label in self.route_app_labels:
            if model_name == 'datadiri':
                return db == 'datadiriall'
        return None
