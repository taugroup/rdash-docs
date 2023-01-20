# FROM python:3
FROM ubuntu

WORKDIR /usr/src/app
COPY . .
COPY config.yml /root

RUN mkdir -p /usr/src/app/Output

RUN chmod u+r+x start.sh \
    && apt update && apt upgrade -y \
    && apt install python3-pip -y \
    && apt install python-is-python3 \
    && pip install pyyaml \
    && pip install pandas \
    && pip install numpy \
    && pip install textract \
    && pip install pyarrow \
    && pip install nltk \
    && python3 -m nltk.downloader stopwords \
    && python3 -m nltk.downloader omw-1.4 \
    && spacy==3.0.0 \
    && pip install yake \
    && pip install rake_nltk \
    # && pip install gensim==3.8.3 \
    && pip install sklearn \
    && pip install sentence_transformers \
    # && python3 -m pip install --upgrade pymupdf==1.18.9 \
    && pip install wordcloud \
    && pip install matplotlib \
    && pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.4.0/en_core_web_sm-3.4.0-py3-none-any.whl \
    && pip install flask==2.0.1 \
    && pip install -U flask-cors \
    && pip install pyecharts \
    && pip install fast-autocomplete \
    && pip install python-Levenshtein \
    && pip install pylev 
    
RUN apt-get install cron -y

ADD cronfile /etc/cron.d/cronfile

RUN chmod 0644 /etc/cron.d/cronfile

RUN crontab /etc/cron.d/cronfile

RUN mkdir -p /usr/src/app/stdout \
    && mkdir -p  /usr/src/app/Output \
    && /usr/bin/python3 /usr/src/app/nltk_downloader.py 

CMD ./start.sh

EXPOSE 9000