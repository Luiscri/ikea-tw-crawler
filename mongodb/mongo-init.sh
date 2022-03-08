set -e

mongo <<EOF
print("Creating crawler user...")
use $MONGO_INITDB_DATABASE
db.createUser({
  user: '$MONGODB_USERNAME',
  pwd: '$MONGODB_PASSWORD',
  roles: [{
    role: "readWrite",
    db: '$MONGO_INITDB_DATABASE'
  }],
});
EOF