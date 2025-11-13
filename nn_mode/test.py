# test.py
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('intfloat/e5-base-v2')
print("Success! Shape:", model.encode("test").shape)