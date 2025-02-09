# Resource Management Service


## Create a Django application within Docker.

1. Create a new folder in services/ where the Django application will reside. Let the name of the service is 'email_service'. So, the base directory will be services/email_service

2. Copy Dockerfile and requirements.txt file in the base directory.

3. Run the following command using docker compose to create the application.

```
docker-compose run email_service django-admin startproject email_service /app
```

4. Remove the temporary docker container created for email service once the django app files get copied over to the volume.

5. Update settings.py file to use the environment variables.

6. Rerun the docker compose file and start the application.





## References

1. [Deploying Django with Docker](https://medium.com/powered-by-django/deploy-django-using-docker-compose-windows-3068f2d981c4)

2. [Authentication and authorization of Django with Keycloak](https://medium.com/@robertjosephk/setting-up-keycloak-in-django-with-django-allauth-cfc84fdbfee2)

3. [Debugging Django application running in docker](https://dev.to/ferkarchiloff/how-to-debug-django-inside-a-docker-container-with-vscode-4ef9)

4. [Debugging Django application running in docker 2](https://testdriven.io/blog/django-debugging-vs-code/)