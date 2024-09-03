
VERSION=`egrep "^version = " ../pyproject.toml | cut -d "=" -f2 | tr -d '[:space:]' | tr -d '"'`

echo "Building version $VERSION"

docker build -t fabiog1901/dbworkload:$VERSION .

docker push fabiog1901/dbworkload:$VERSION

docker build -t fabiog1901/dbworkload .

docker push fabiog1901/dbworkload

#docker image rm fabiog1901/dbworkload:v0.2.2
#docker image rm fabiog1901/dbworkload

#docker run --rm fabiog1901/dbworkload --version
