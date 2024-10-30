from django.db import models

# Create your models here.
class GithubRepository:
    def __init__(self, name:str, title:str, url:str, description:str='', icon:str=''):
        self.name = name
        self.title = title
        self.description = description
        self.icon = icon
        self.url = url