import firebase_admin
from firebase_admin import credentials, firestore

# Global Firestore client instance
firestore_db = None

def get_firestore_db():
    global firestore_db

    if not firebase_admin._apps:  # Initialize Firebase only once
        cred = credentials.Certificate("mews-project-firebase-adminsdk-fbsvc-1730ff6a5b.json")  # Your Firebase JSON file
        firebase_admin.initialize_app(cred)

    if firestore_db is None:  # Initialize Firestore client only once
        firestore_db = firestore.client()
    
    return firestore_db


# import firebase_admin
# from firebase_admin import credentials, firestore

# cred = credentials.Certificate("firebase_adminsdk.json")  # Your Firebase JSON file
# firebase_admin.initialize_app(cred)

# db = firestore.client()

# def add_data(collection, doc_id, data):
#     """ Add data to Firestore """
#     db.collection(collection).document(doc_id).set(data)

# def get_data(collection, doc_id):
#     """ Retrieve data from Firestore """
#     doc = db.collection(collection).document(doc_id).get()
#     return doc.to_dict() if doc.exists else None

# def get_all_data(collection):
#     """ Retrieve all documents from a Firestore collection """
#     docs = db.collection(collection).stream()
#     return {doc.id: doc.to_dict() for doc in docs}

# def update_data(collection, doc_id, data):
#     """ Update existing document in Firestore """
#     db.collection(collection).document(doc_id).update(data)

# def delete_data(collection, doc_id):
#     """ Delete document from Firestore """
#     db.collection(collection).document(doc_id).delete()