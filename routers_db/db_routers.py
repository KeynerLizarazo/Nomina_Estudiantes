import logging
from django.db import connections, OperationalError

class AuthRouter:
    """
    AuthRouter es un router de bases de datos personalizado para Django.
    Su objetivo es dirigir las operaciones de lectura, escritura, relaciones y migraciones
    de las aplicaciones internas de Django (como auth, admin, sessions, etc.) a una base de datos específica ('local_db').
    """

    # Conjunto de etiquetas de aplicaciones que serán dirigidas a 'local_db'
    route_app_labels = {'admin', 'contenttypes', 'sessions', 'auth', 'messages', 'staticfiles'}

    # Puedes definir una lista de preferencia de bases de datos
    preferred_dbs = ['default', 'local_db']
    
    def _get_available_db(self):
        """
        Devuelve la primera base de datos disponible según el orden de preferred_dbs.
        """
        for db in self.preferred_dbs:
            try:
                # Intenta abrir una conexión (no ejecuta queries)
                connections[db].ensure_connection()
                return db
            except OperationalError:
                logging.warning(f"Base de datos '{db}' no disponible.")
        # Si ninguna está disponible, retorna None
        return None
    
    def db_for_read(self, model, **hints):
        """
        Indica a Django que las operaciones de lectura (SELECT) para los modelos de las apps internas
        deben hacerse en la base de datos 'local_db'.
        """
        if model._meta.app_label in self.route_app_labels:
            return 'local_db'
        return None

    def db_for_write(self, model, **hints):
        """
        Indica a Django que las operaciones de escritura (INSERT, UPDATE, DELETE) para los modelos de las apps internas
        deben hacerse en la base de datos 'local_db'.
        """
        if model._meta.app_label in self.route_app_labels:
            return 'local_db'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """
        Permite relaciones entre modelos si al menos uno de ellos pertenece a las apps internas de Django.
        Esto es útil para permitir relaciones entre usuarios, permisos, sesiones, etc.
        """
        if (
            obj1._meta.app_label in self.route_app_labels or
            obj2._meta.app_label in self.route_app_labels
        ):
            return True
        return False

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Indica a Django que las migraciones (creación/modificación de tablas) de las apps internas
        solo deben aplicarse en la base de datos 'local_db'.
        """
        if app_label in self.route_app_labels:
            return db == 'local_db'
        return None