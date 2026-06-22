from redis import Redis
from rq import Worker, Queue
import os

if __name__ == '__main__':
    redis = Redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
    Worker([Queue('default', connection=redis)], connection=redis).work()
