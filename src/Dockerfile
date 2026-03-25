FROM python:3.13-slim

# Update OS packages to fix vulnerabilities
RUN apt-get update && apt-get upgrade -y && apt-get clean

WORKDIR /code

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]