FROM python:3.9-slim

RUN pip install --upgrade --no-cache-dir pip pymongo==4.0.1 uvicorn[standard]==0.16.0 fastapi==0.70.1

COPY unifi_vouchers.py /opt/

EXPOSE 8000/tcp

WORKDIR /opt/

CMD ["uvicorn", "unifi_vouchers:app", "--host", "0.0.0.0", "--port", "8000"]
