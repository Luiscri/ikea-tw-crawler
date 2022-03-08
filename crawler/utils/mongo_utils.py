import os

MONGODB_COLLECTION = os.environ.get('MONGODB_COLLECTION')

def get_by_ids(db, ids):
    """Method which retrieves from a mongodb collection the tweets contained in
    the list given as a parameter.

    Parameters
    ----------
    db: pymongo.database.Database
        MongoDB client used to create the connection and retrieve the data.
    ids: list[int]
        List of ids to retrieve.
    """
    return db[MONGODB_COLLECTION].find(
        {'_id': {'$in': ids}},
        {'_id': 0, 'created_at': 1, 'text': 1, 'interactions': 1}    
    )