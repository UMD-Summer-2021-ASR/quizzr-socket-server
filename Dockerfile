FROM  tensorflow/tensorflow  
COPY ./ ./
RUN python -m pip install -r requirements.txt
CMD ["python" , "main.py"]