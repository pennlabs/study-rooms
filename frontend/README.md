# portal

A web-based portal for organizations to reach Penn Mobile users.

## setting up

1. Start the backend
   ```python
   cd penn-mobile/backend
   pipenv install --dev
   pipenv run python manage.py migrate
   pipenv run python manage.py runserver 8000
   ```
1. Navigate to `/frontend`
   ```
   yarn install
   export NODE_OPTIONS=--openssl-legacy-provider
   yarn dev
   ```
   you should be able to see the site at `localhost:3000`!
1. The backend should be running at `localhost:8000`. We proxy all requests from localhost:3000/api to localhost:8000/api (in `frontend/server.js`), so you can make requests to the backend from the frontend. If you want to directly see what the request should return, you can go to `localhost:8000/api/...` to see the response.
1. There's also some jankiness with login since we make requests to clubs and accounts -- for login to work in your dev environment, you'll need to go to `localhost:8000/admin` and add a valid access token (make sure the expiration date is some day in the far future).

kek