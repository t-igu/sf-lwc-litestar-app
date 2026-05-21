import jwt

with open("secret_key/sf_private_key.pem") as f:
    key = f.read()

print(jwt.encode({"test": 123}, key, algorithm="RS256"))
