from typing import List, Optional
from django.core.cache import cache, caches
from django.http import HttpRequest

class GQLCachingService:
    """
    This service implements custom caching for GraphQL queries.
    """
    GQL_CACHE_KEY_PREFIX = "gql_cache__"
    VARY_CACHE_BY_ARGS = "args"
    VARY_CACHE_BY_USERAGENT = "useragent"
    VARY_CACHE_BY_IP = "ip"
    VARY_CACHE_BY_USER = "user"

    def __init__(self):
        pass

    # Cache keys
    def __construct_key_name(self, key):
        """
        Construct the key name for the cache.
        @param key: str - The key to construct the cache key name from.
        """
        return self.GQL_CACHE_KEY_PREFIX + key
    
    def __construct_cache_by_args(self, key:str, args:List[str]):
        """
        Construct the key name for the cache by arguments.
        @param key: str - The key to construct the cache key name from.
        @param args: List[str] - The arguments to construct the cache key name from.
        """
        if args is None:
            args = []

        return "_".join(args)
    
    def __construct_cache_by_useragent_key_name(self, key:str, useragent:str):
        """
        Construct the key name for the cache by user agent.
        @param key: str - The key to construct the cache key name from.
        @param useragent: str - The user agent to construct the cache key name from.
        """
        return key + "_" + useragent
    
    def __construct_cache_by_ip_key_name(self, key:str, ip:str):
        """
        Construct the key name for the cache by IP address.
        @param key: str - The key to construct the cache key name from.
        @param ip: str - The IP address to construct the cache key name from.
        """
        return key + "_" + ip
    

    def __construct_cache_by_user_key_name(self, key:str, user:str):
        """
        Construct the key name for the cache by user.
        @param key: str - The key to construct the cache key name from.
        @param user: str - The user to construct the cache key name from.
        """
        return key + "_" + user
    
    # Cache data extractor
    def __retrieve_user_agent(self, request:HttpRequest):
        """
        Retrieve the user agent from the request.
        @param request: HttpRequest - The request object to retrieve the user agent from.
        """
        if not request:
            return None
        
        useragent = request.META.get("HTTP_USER_AGENT", None)
        if not useragent:
            useragent = request.META.get("USER_AGENT", None)
        return useragent

    
    def __retrieve_current_user_identifier(self, request:HttpRequest):
        """
        Retrieve the current user identifier from the request.
        @param request: HttpRequest - The request object to retrieve the current user identifier from.
        """
        if not request or not request.user or not request.user.is_anonymous:
            return None
        
        return request.user.get_username()
    
    # Get
    def __get_cache(self, key: str):
        """
        Get cache from Django cache.
        @param key: str - The key to retrieve from cache.
        """
        
        return cache.get(self.__construct_key_name(key))
    
    def __exists(self, key: str):
        """
        Check if cache exists in Django cache.
        @param key: str - The key to check in cache.
        """
        return self.__get_cache(key) is not None
    

    # Set
    def __set_cache(self, key: str, value: str, expiration: int):
        """
        Set cache in Django cache.
        @param key: str - The key to set in cache.
        @param value: str - The value to set in cache.
        @param expiration: int - The expiration time for the cache.
        """
        cache.set(self.__construct_key_name(key), value, expiration)


    # Remove
    def __remove_cache(self, key: str):
        """
        Remove cache from Django cache.
        @param key: str - The key to remove from cache.
        """
        cache.delete(self.__construct_key_name(key))
    

    # High level methods
    def get_unique_key(self, prefix:str, request:HttpRequest, args:Optional[List[str]]=[], vary_on:List[str]=[]):
        """
        A high level method to get a unique key for the cache.
        @param prefix: str - A cache prefix.
        @param request: HttpRequest - The request object to retrieve the cache from.
        @param args: Optional[tuple] - The arguments to retrieve the cache from.
        @param vary_on: List[str] - The list of values to vary the cache on.
        """
        if not vary_on or not request:
            return prefix
        
        unique_key = prefix if prefix + "__" else ""
        for vary in vary_on:
            if vary == self.VARY_CACHE_BY_ARGS:
                unique_key += self.__construct_cache_by_args("", args)
            elif vary == self.VARY_CACHE_BY_USERAGENT:
                unique_key += self.__construct_cache_by_useragent_key_name("", self.__retrieve_user_agent(request))
            elif vary == self.VARY_CACHE_BY_IP:
                unique_key += self.__construct_cache_by_ip_key_name("", request.META.get("REMOTE_ADDR", None))
            elif vary == self.VARY_CACHE_BY_USER:
                unique_key += self.__construct_cache_by_user_key_name("", self.__retrieve_current_user_identifier(request))
        return unique_key
    
    def cache_exists(self, prefix:str, request:HttpRequest, args:Optional[tuple]=(), vary_on:List[str]=[]):
        """
        A high level method to check if cache exists.
        @param request: HttpRequest - The request object to check the cache from.
        @param args: Optional[tuple] - The arguments to check the cache from.
        @param vary_on: List[str] - The list of values to vary the cache on.
        @param prefix: str - The prefix to add to the unique key.
        """
        if not vary_on or not request:
            return self.__get_cache(prefix) is not None
        
        unique_key = self.get_unique_key(prefix, request, args, vary_on, prefix)
        return self.__exists(unique_key)
    
    
    def retrieve(self, prefix:str, request:HttpRequest, args:Optional[List[str]]=[], vary_on:List[str]=[]):
        """
        A high level method to retrieve cache.
        @param request: HttpRequest - The request object to retrieve the cache from.
        @param args: Optional[tuple] - The arguments to retrieve the cache from.
        @param vary_on: List[str] - The list of values to vary the cache on.
        @param prefix: str - The prefix to add to the unique key.
        """
        if not vary_on or not request:
            return self.__get_cache(prefix)
        
        unique_key = self.get_unique_key(prefix, request, args, vary_on, prefix)
        return self.__get_cache(unique_key)
    
    def store(self, prefix:str, value:str, request:HttpRequest, args:Optional[List[str]]=[], vary_on:List[str]=[], expiration:int=60*15):
        """
        A high level method to store cache.
        @param value: str - The value to store in cache.
        @param expiration: int - The expiration time for the cache [Default: 15 minutes].
        @param request: HttpRequest - The request object to store the cache from.
        @param args: Optional[tuple] - The arguments to store the cache from.
        @param vary_on: List[str] - The list of values to vary the cache on.
        @param prefix: str - The prefix to add to the unique key.
        """
        if not vary_on or not request:
            return self.__set_cache(prefix, value, expiration)
        
        unique_key = self.get_unique_key(prefix, request, args, vary_on, prefix)
        return self.__set_cache(unique_key, value, expiration)
    
    def remove(self, prefix:str, request:HttpRequest, args:Optional[List[str]]=[], vary_on:List[str]=[]):
        """
        A high level method to remove cache.
        @param request: HttpRequest - The request object to remove the cache from.
        @param args: Optional[tuple] - The arguments to remove the cache from.
        @param vary_on: List[str] - The list of values to vary the cache on.
        @param prefix: str - The prefix to add to the unique key.
        """
        if not vary_on or not request:
            return self.__remove_cache(prefix)
        
        unique_key = self.get_unique_key(prefix, request, args, vary_on, prefix)
        return self.__remove_cache(unique_key)
    
    


        