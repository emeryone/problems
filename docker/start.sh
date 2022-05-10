app="emery.problems"
docker build -t ${app} .
docker run -d -p 56733:80 --restart=always -v $PWD/../app:/app --name ${app} ${app}