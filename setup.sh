#!/bin/bash
echo "=== Kéo Docker SQL Server ==="
docker pull mcr.microsoft.com/mssql/server:2022-latest

echo "=== Chạy SQL Server ==="
docker run -e "ACCEPT_EULA=Y" \
  -e "MSSQL_SA_PASSWORD=Vietnam@123" \
  -p 1433:1433 \
  --name sqlserver \
  -d mcr.microsoft.com/mssql/server:2022-latest

echo "=== Cài thư viện ODBC ==="
sudo apt-get update
curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
curl https://packages.microsoft.com/config/ubuntu/22.04/prod.list | sudo tee /etc/apt/sources.list.d/mssql-release.list
sudo apt-get update
sudo ACCEPT_EULA=Y apt-get install -y msodbcsql17
sudo apt-get install -y unixodbc-dev

echo "=== Cài thư viện Python ==="
pip install -r requirements.txt

echo "=== Hoàn tất! ==="
