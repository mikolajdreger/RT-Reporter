<h1 align="center">RT-Reporter</h1>

## About The Project
<br />
<div align="center">
  <a href="">
    <img src="./web1.png" alt="Logo" width="800px" height="600px">
  </a>
</div>
RT-Reporter is a tool dedicated to creating reports in PDF format for the Request Tracker tool - a tool dedicated to handling tickets, in the case of SOC/CERT teams to respond to security incidents. The RT-Reporter tool is built based on Flask and HTML and CSS. The version presented in this repository creates a simple summary of handled incidents in the time period declared by the user.
The tool has a built-in authentication mechanism.

## Getting Started
Below I'll give you information on how to properly run the tool on your Request Tracker instance.

### Prerequisites
The tool works with a mysql database, it uses a database dedicated to Request Tracker, which is rt5. For security reasons, the tool uses a low-privileged mysql user account, which you must create and grant permissions to. You can do it in a simple way:

* mysql login
  ```sh
  mysql -u root -p
  ```
* mysql user creation
  ```sh
  CREATE USER 'reporter'@'localhost' IDENTIFIED BY 'password';
  ```
* Granting permissions
  ```sh
  GRANT SELECT on rt5.Tickets TO 'reporter'@'localhost' WITH GRANT OPTION;  
  ```
  ```sh
  FLUSH PRIVILEGES;
  ```


### Installation

First, clone this repository, then install the modules from the requirements.txt file. Finally, run the application.

1. Clone the repo
   ```sh
   git clone https://github.com/mikolajdreger/RT-Reporter.git
   ```
3. Install requirements.txt
   ```sh
   pip3 install -r requirements.txt
   ```
4. Run the application. 
   Test env:

   ```sh
   python3 app.py
   ```
   Prod env:
   ```sh
   apt install gunicorn -y
   ```
   ```sh
   gunicorn -w 4 --bind 0.0.0.0:8080 app:app 
   ```
