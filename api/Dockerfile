FROM python:3
COPY . /usr/src/app
RUN pip3 install -r /usr/src/app/requirements.txt
RUN pip3 install pymongo
CMD ["python3", "/usr/src/app/api_2.py"]
