# RideShare
Cloud Computing Assignment 1

## Cloud Deployment

### Step 1 - Installing the Components from the Ubuntu Repositories
```shell script
$ sudo apt update
$ sudo apt install python3-pip python3-dev build-essential libssl-dev libffi-dev python3-setuptools nginx python3-venv
```

### Step 2 - Activating Python Virtual Environment
```shell script
$ git clone https://github.com/G0uth4m/RideShare.git
$ cd Rideshare
$ python3.6 -m venv venv/
$ source venv/bin/activate
```

### Step 3 - Setting Up a Flask Application
```shell script
(venv) $ pip install -r requirements.txt
(venv) $ deactivate
```

### Step 4 - Configuring MongoDB
```shell script
$ sudo apt install mongodb
$ sudo nano /etc/mongodb.conf
bind_ip = 0.0.0.0
port = 27017
ath=true
$ mongo
> use rideshare
> db.createUser({
  user: '<username>',
  pwd: '<password>',
  roles: [{
    role: 'readWrite',
    db: 'rideshare'  
  }]
})
> exit
$ sudo serive mongodb restart
```

### Step 5 - Configuring Gunicorn
```shell script
$ sudo nano /etc/systemd/system/rideshare.service
[Unit]
Description=Gunicorn instance to serve rideshare
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/RideShare
Environment="PATH=/home/ubuntu/RideShare/venv/bin"
ExecStart=/home/ubuntu/RideShare/venv/bin/gunicorn --workers 3 --bind unix:rideshare -m 007 wsgi:app

[Install]
WantedBy=multi-user.target
$ sudo systemctl start rideshare
$ sudo systemctl enable rideshare
```

### Step 6 - Configuring Nginx to Proxy Requests
```shell script
$ sudo nano /etc/nginx/sites-available/rideshare
server {
    listen 80;
    server_name your_domain www.your_domain;

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/ubuntu/RideShare/rideshare.sock;
    }
}
$ sudo ln -s /etc/nginx/sites-available/rideshare /etc/nginx/sites-enabled
$ sudo systemctl restart nginx
```

## Authors
* **Goutham** - [G0uth4m](https://github.com/G0uth4m)
* **Monish Reddy** - [MONISHREDDYBS](https://github.com/MONISHREDDYBS)