FROM ubuntu:18.04
# RUN apt-get update && apt-get install -y mysql-server
RUN apt update &&  apt upgrade -y
RUN apt install -y python3 python3-pip
# RUN apt install -y python3 python3-pip libnvvm3 cuda-toolkit-11-2
# RUN apt install -y mysql-server
WORKDIR /app
ADD . /app
RUN pip3 install --upgrade pip
RUN pip3 install gunicorn==20.1.0
RUN pip3 install -r req.txt
EXPOSE 5002
# CMD [ "python3", "flaskApp.py" ]
CMD ["gunicorn", "-b", ":5002", "fwsgi:app", "--timeout", "3000", "--workers", "1"]