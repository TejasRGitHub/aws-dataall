# Managing DB with Alembic locally
In data.all we use [Alembic](https://alembic.sqlalchemy.org/en/latest/)  -- a lightweight database migration tool for usage with the SQLAlchemy Database Toolkit for Python.
Alembic relies on the database's current state to generate and apply migrations accurately.
Alembic determines the changes to be made by comparing the current state of the database with the desired state specified in your SQLAlchemy models. This process, known as schema diffing, requires an existing database to identify differences.
Alembic generates migration scripts based on the detected differences between the current database schema and the desired schema defined in your application code. This generation is dependent on the actual structure and content of the database.

In order to create and test migrations locally you will have to create a local database.

## Prerequisites

1. Build and launch Docker containers for the database and GraphQL. 
```bash
docker compose build db
docker compose run db
docker compose build graphql
docker compose run graphql
```
These can also be initiated alongside all local testing containers using the following command:
```bash
docker compose up
```
2. Specify the location of database model descriptions. If you are at the project's root, the target folder path is backend.
```bash
export PYTHONPATH=backend
```
3. The containers initiated in the first step will default to using the schema named `dkrcompose`. In order to freely experiment with database let's create new schema 'local'. Alembic relies on the environmental variable `envname` to determine the schema. Set it to `local` with the following command:
```bash
export envname=local
```
In a real-life RDS database, `envname` adopts the value of the environment (e.g., dev, test, etc.).
If you want to apply the same migrations against your db schema that is used in local data.all deployments, you should use schema `dkrcompose`.
```bash
export envname=dkrcompose
```

## Managing migrations

When we run ```docker compose build``` the postgres container is created with no tables or schemas.

Upon start of GraphQL container, sqlalchemy ```declarative_base``` is used to create all tables with this function: 
```Base.metadata.create_all(engine.engine)```. **The number of tables depends on the modules that are enabled in ```config.json``` (in the root of the project).**

As the database is created from scratch, it has no current information about migration state, so, first we need to run database upgrade.
After that alembic will be able to generate the further migrations locally.

This command will apply all migrations, and syncronize the DB state with local alembic history of migrations.
```bash
make upgrade-db 
```
or
```bash
alembic -c backend/alembic.ini upgrade head
```

To upgrade database and generate alembic migration during development use:

```bash
make generate-migrations
```
or
```bash
alembic -c backend/alembic.ini upgrade head
alembic -c backend/alembic.ini revision -m "describe_changes_shortly" --autogenerate
```
Please, change the auto-generated filename postfix with the short description of the migration purpose. Also, rename this prefix in the file itself (first line)
Always check autogenerated migration file to ensure that necessary changed are reflected there.

## What to know about autogenerated migrations:

**Autogenerate will detect:**

 - Table additions, removals. 
 - Column additions, removals.
 - Change of nullable status on columns.
 - Basic changes in indexes and explicitly-named unique constraints
 - Basic changes in foreign key constraints

**Autogenerate can optionally detect:**

 - Change of column type. This will occur by default unless the parameter `EnvironmentContext.configure.compare_type` is set to `False`. The default implementation will reliably detect major changes, such as between `Numeric` and `String`, as well as accommodate for the types generated by SQLAlchemy’s “generic” types such as `Boolean`. Arguments that are shared between both types, such as length and precision values, will also be compared. If either the metadata type or database type has additional arguments beyond that of the other type, these are not compared, such as if one numeric type featured a “scale” and other type did not, this would be seen as the backing database not supporting the value, or reporting on a default that the metadata did not specify.

The type comparison logic is fully extensible as well; see [Comparing Types](https://alembic.sqlalchemy.org/en/latest/autogenerate.html#compare-types) for details.

 - Change of server default. This will occur if you set the `EnvironmentContext.configure.compare_server_default` parameter to `True`, or to a custom callable function. This feature works well for simple cases but cannot always produce accurate results. The Postgresql backend will actually invoke the “detected” and “metadata” values against the database to determine equivalence. The feature is off by default so that it can be tested on the target schema first. Like type comparison, it can also be customized by passing a callable; see the function’s documentation for details.

**Autogenerate can not detect:**

- Changes of table name. These will come out as an add/drop of two different tables, and should be hand-edited into a name change instead.
  In this case you should remove the automatically generated scripts and replace them with the following code (e.g. renaming table 'marathon' to 'snickers):
  ```python
    def upgrade():
        op.rename_table('marathon', 'snickers')
        op.execute('ALTER SEQUENCE marathon_id_seq RENAME TO snickers_id_seq') # don't forget to rename all related entities
        op.execute('ALTER INDEX marathon_pkey RENAME TO snickers_pkey')
    
    def downgrade():
        op.rename_table('snickers', 'marathon')
        op.execute('ALTER SEQUENCE snickers_id_seq RENAME TO marathon_id_seq')
        op.execute('ALTER INDEX snickers_pkey RENAME TO marathon_pkey')
  ```
- Changes of column name. Like table name changes, these are detected as a column add/drop pair, which is not at all the same as a name change. 
  To keep all data in the column add this script to upgrade function (and don't forget to add inverse in downgrade function)
  ```python
  with op.batch_alter_table('my_table', schema=None) as batch_op: batch_op.alter_column('old_col_name', new_column_name='new_col_name')
  ```
- Anonymously named constraints. Give your constraints a name, e.g. `UniqueConstraint('col1', 'col2', name="my_name")`. See the section The [Importance of Naming Constraints ](https://alembic.sqlalchemy.org/en/latest/naming.html)for background on how to configure automatic naming schemes for constraints. 
- Special SQLAlchemy types such as Enum when generated on a backend which doesn’t support ENUM directly - this because the representation of such a type in the non-supporting database, i.e. a CHAR+ CHECK constraint, could be any kind of CHAR+CHECK. For SQLAlchemy to determine that this is actually an ENUM would only be a guess, something that’s generally a bad idea. To implement your own “guessing” function here, use the `sqlalchemy.events.DDLEvents.column_reflect()` event to detect when a CHAR (or whatever the target type is) is reflected, and change it to an ENUM (or whatever type is desired) if it is known that that’s the intent of the type. `The sqlalchemy.events.DDLEvents.after_parent_attach()` can be used within the autogenerate process to intercept and un-attach unwanted CHECK constraints. 
  As example of handling Enums, please refer to  `ConfidentialityClassification` in migration `97050ec09354_release_3_7_8.py`


**Autogenerate can’t currently, but will eventually detect:**
- Some free-standing constraint additions and removals may not be supported, including PRIMARY KEY, EXCLUDE, CHECK; these are not necessarily implemented within the autogenerate detection system and also may not be supported by the supporting SQLAlchemy dialect. 
- Sequence additions, removals - not yet implemented.


## Why alembic didn't add my new models into migration
For not yet detected reason alembic is 'blind' towards some files with models definition. If your new model is not added to migration file,
try import its class explicitly into file 'backend/migrations/env.py' under the line '# import additional models here'.


https://alembic.sqlalchemy.org/en/latest/