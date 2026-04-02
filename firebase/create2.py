import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

doc = {
  "name": "盧安毅",
  "mail": "s1101680@pu.edu.tw",
  "lab": 888
}

doc_ref = db.collection("靜宜資管2026B").document("andylu")
doc_ref.set(doc)