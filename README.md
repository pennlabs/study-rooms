# penn-mobile

[![Build and Deploy](https://github.com/pennlabs/penn-mobile/actions/workflows/cdkactions_build-and-deploy.yaml/badge.svg)](https://github.com/pennlabs/penn-mobile/actions/workflows/cdkactions_build-and-deploy.yaml)
[![Coverage Status](https://codecov.io/gh/pennlabs/penn-mobile/branch/master/graph/badge.svg)](https://codecov.io/gh/pennlabs/penn-mobile)

This repository is the Django-based successor to `labs-api-server`, containing API routes to help students manage and keep track of things around campus that matter to them. This repo contains:

- GSR Booking
- Laundry Data
- Dining Data
- Fitness Data
- News and Events
- Posts and Polls
- Notifications

## Install

- `git clone https://github.com/pennlabs/penn-mobile.git`
- `cd penn-mobile/backend`
- `brew install postgres`
- `pipenv install --dev --python 3.11`

Note that the above command will likely throw some ugly errors at you with regards to the `psycopg2` packages. If that is the case, just manually install them:
- `pipenv install psycopg2`
- `pipenv install --dev`

Final Steps:
- `pipenv run python manage.py migrate`
- `pipenv run python manage.py runserver 8000`

Making git blame [correct](https://github.com/pennlabs/penn-mobile/pull/287) (_optional_):
- `git config blame.ignoreRevsFile .git-blame-ignore-revs`

Setting up precommit (_optional_):
- `pipenv run pre-commit install`

### Nix Development Environment
If you have Nix installed, you can use `nix develop` in `./backend` to set up a currently partial development environment for you. Note commands such as `pipenv run python manage.py migrate` become `python manage.py migrate` as `nix develop` puts one's shell directly in the development environment and this is currently only configured for x84_64 Linux. It does work on WSL. I have no idea if it works on MacOS.

## Creating Users

To create users, you first have to create a main superuser.

- `pipenv run python manage.py createsuperuser` and follow the instructions
- Then, you can go to `localhost:8000/admin/auth/user/add/` to add more users.

## Testing Delayed Notifications
- `brew install redis`

In separate terminal windows, run the following commands:
- `redis-server`
- `celery -A pennmobile worker -linfo`

## Exploring the API

- Expore the API via our [auto-generated documentation](https://pennmobile.org/api/documentation/)! This is a really good way to click around and discover stuff.
