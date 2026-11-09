from django.db.backends.mysql.base import DatabaseWrapper as MySQLDatabaseWrapper
from django.db.backends.mysql.schema import DatabaseSchemaEditor as MySQLSchemaEditor


class DatabaseSchemaEditor(MySQLSchemaEditor):
    # TiDB validates both clauses against the schema before ALTER TABLE.
    # Let Django add the foreign key separately after creating the column.
    sql_create_column_inline_fk = None


class DatabaseWrapper(MySQLDatabaseWrapper):
    SchemaEditorClass = DatabaseSchemaEditor
