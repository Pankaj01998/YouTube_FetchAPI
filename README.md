# YouTube_FetchAPI

To run this repository, first clone the repository and go into that directory of repository

Now first build the docker image using command

```
sudo docker build -t dckr-img .
```

After building the image, create the container using the command
```
sudo docker run -d --name dckr-container -v $(pwd):/app -p 5022:5002 dckr-img
```

This will run the flask app on port number 5022 of server.
