from nameko.extensions import DependencyProvider
import redis

#TODO - Validate client
class RedisClient(DependencyProvider):

    def setup(self):
        config = self.container.config
        redis_uri = config.get('REDIS_CACHE_URI')
        self.client = redis.StrictRedis.from_url(redis_uri)

    def get_dependency(self, worker_ctx):
        return self.client
