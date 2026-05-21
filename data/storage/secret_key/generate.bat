openssl genrsa -out sf_private_key.pem 2048
openssl rsa -in sf_private_key.pem -pubout -out sf_public_key.pem