"""
    Strings
"""

APP_INFO = """
With help of this application you can easy generate SQL scripts based on simple table description.
Fist step is to create table definision in xml format and after it you can generate SQLs.
You can find examples below.
"""

TABLE_DESCRIPTION_EXAMPLE = """
**Example 1 (as description):**
```
User table has id, name (not empty, string, maximum 100 chars). User has also e-mail (unique).
We should register last login time.
User has flags for daily and weekly subscriptions.
Flag locked means that user can't login into system.
```
**Example 2 (as set of fields):**
```
Channel
id
name
creation date
created by 
```

**Example 3 (creative):**
```
Table user with common fields.
```

**Example of Table rules:**
```
Field contains:
- correct database field name based on Postgres notation
- field type based on Postgres types
- primary_key (if true, default value is false)
- not_null (if true, default value is false)
- unique (if true, default value is false)
- foreign_key (if field is id for another table)
```

**Example of Script definition:**
```
1. CREATE TABLE script
2. Stored procedures to create (return new id) 
3. Stored procedures to update by id (return True if success)
4. Stored procedures to delete by id (return True if success)
5. Stored procedures to get by id
6. View and stored procedures to get all items
```

"""