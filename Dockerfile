FROM python:3.10-slim-bullseye  # or python:3.10-slim-bookworm

RUN apt update && apt upgrade -y
RUN apt install git -y
COPY requirements.txt /requirements.txt

RUN pip3 install -U pip && pip3 install -U -r requirements.txt
RUN mkdir /RX-AUTOFILER2
WORKDIR /RX-AUTOFILER2
COPY . /RX-AUTOFILER2
CMD ["python", "bot.py"]
