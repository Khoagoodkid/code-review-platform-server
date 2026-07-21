from sqlalchemy import inspect

def object_to_dict(obj):
    if not obj:
        return None
    return {c.key: getattr(obj, c.key) for c in inspect(obj).mapper.column_attrs}
