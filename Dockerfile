FROM python:3.8-buster
COPY ./ ./
RUN python -m pip install -r requirements.txt
CMD ["python" , "main.py"]