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

After running the flask app you can use the following API mentioned in the flask app which are

1) **query_all** : GET API which returns the stored video data in a paginated response sorted in descending order of published datetime
2) **search** : search API to search the stored videos using their title and description
3) **quota_status** : API to check quota status of API key
4) **gen_key** : API for supplying multiple API keys so that if quota is exhausted on one, it can generate another key and will use that key
