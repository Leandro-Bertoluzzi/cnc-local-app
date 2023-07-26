<h1 align="center">CNC manager</h1>

<p align="center">
  <img alt="Github top language" src="https://img.shields.io/github/languages/top/Leandro-Bertoluzzi/cnc-admin?color=56BEB8">

  <img alt="Github language count" src="https://img.shields.io/github/languages/count/Leandro-Bertoluzzi/cnc-admin?color=56BEB8">

  <img alt="Repository size" src="https://img.shields.io/github/repo-size/Leandro-Bertoluzzi/cnc-admin?color=56BEB8">

  <img alt="License" src="https://img.shields.io/github/license/Leandro-Bertoluzzi/cnc-admin?color=56BEB8">
</p>

<!-- Status -->

<h4 align="center">
	🚧 CNC manager 🚀 Under construction...  🚧
</h4>

<hr>

<p align="center">
  <a href="#dart-about">About</a> &#xa0; | &#xa0;
  <a href="#sparkles-features">Features</a> &#xa0; | &#xa0;
  <a href="#rocket-technologies">Technologies</a> &#xa0; | &#xa0;
  <a href="#white_check_mark-requirements">Requirements</a> &#xa0; | &#xa0;
  <a href="#checkered_flag-starting">Starting</a> &#xa0; | &#xa0;
  <a href="#memo-license">License</a> &#xa0; | &#xa0;
  <a href="https://github.com/Leandro-Bertoluzzi" target="_blank">Authors</a>
</p>

<br>

## :dart: About ##

Desktop application to monitor and manage an Arduino-based CNC machine connected to the local machine.

## :sparkles: Features ##

:heavy_check_mark: GUI\
:heavy_check_mark: MySQL database management\
:heavy_check_mark: G-code files management\
:heavy_check_mark: Real time monitoring of CNC status\
:heavy_check_mark: Communication with GRBL-compatible CNC machine via USB\
:heavy_check_mark: Long-running process delegation via message broker

## :rocket: Technologies ##

The following tools were used in this project:

- [Python](https://www.python.org/)
- [PyQt](https://wiki.python.org/moin/PyQt)
- [Mysql](https://www.mysql.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/) and [Alembic](https://alembic.sqlalchemy.org/en/latest/)
- [Celery](https://docs.celeryq.dev/en/stable/)
- [Redis](https://redis.io/)
- [Docker](https://www.docker.com/)

## :white_check_mark: Requirements ##

Before starting :checkered_flag:, you need to have [Python](https://www.python.org/) installed.

## :checkered_flag: Development ##

```bash
# Clone this project
$ git clone https://github.com/Leandro-Bertoluzzi/cnc-admin

# 1. Access the repository
$ cd cnc-admin

# 2. Set up your Python environment
# Option 1: If you use Conda
conda env create -f conda/environment-dev.yml
conda activate cnc-admin-dev

# Option 2: If you use venv and pip
$ python -m venv env-dev
# Activate your environment according to your OS:
# https://docs.python.org/3/tutorial/venv.html
$ pip install -r pip/requirements-dev.txt

# 3. Copy and (optionally) configure the .env file
cp .env.example .env

# 4. Run Docker to start the DB, PHPMyAdmin, the
# CNC worker (Celery) and its Message broker (Redis)
$ docker-compose up

# 5. If you are starting a new DB, run DB migrations
$ alembic upgrade head

# 6. Start the app
$ python main.py
```

If you are developing on Windows, the docker-compose file won't work since ***devices*** is not able to map Windows ports to Linux containers. Options are:
1. Use a virtual machine with a Linux distribution.
2. In step 4, remove the service `worker` from the file `docker-compose.yaml` before running `docker-compose up`.
3. Don't use docker-compose at all and start MySQL and Redis the common way, or with `docker run` (see [Deployment](#deployment) section for more information).

In either cases 2 and 3, you will need to start the CNC worker by following the steps:
```bash
# Set up your Python environment
# Option 1: If you use Conda
conda env create -f conda/environment-dev-windows.yml
conda activate cnc-admin-dev

# Option 2: If you use venv and pip
$ python -m venv env-dev
$ .\env\Scripts\activate
$ pip install -r pip/requirements-dev-windows.txt

# (optional) Start the MySQL server with Docker
$ docker run -d -p 3306:3306 --env-file=mysql/.env mysql:5.7

# (optional) Start the Redis server with Docker
$ docker run -d -p 6379:6379 redis

# Start Celery's worker server
$ celery --app tasks worker --loglevel=INFO --logfile=logs/celery.log --pool=gevent
```

## :wrench: Running tests ##

```bash
$ pytest -s
```

If you want to update the coverage report (available in /htmlcov):

```bash
$ pytest -s --cov=. --cov-report=html
```

## :memo: License ##

This project is under license from MIT. For more details, see the [LICENSE](LICENSE.md) file.

## :writing_hand: Authors ##

Made with :heart: by <a href="https://github.com/Leandro-Bertoluzzi" target="_blank">Leandro Bertoluzzi</a> and Martín Sellart.

<a href="#top">Back to top</a>
