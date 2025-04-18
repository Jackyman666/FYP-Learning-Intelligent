# job_store.py
import redis, os, json
from typing import Any, Dict, Optional
from config import REDIS_STORE_TIME
from dotenv import load_dotenv

load_dotenv()

# job format:
# {
#     "uuid123": {"status":"Start generation"}
# }
class JobStoreManager:
    def __init__(self):
        self.client = redis.StrictRedis(
            host=os.getenv("REDIS_HOST"),
            port=6380,
            password=os.getenv("REDIS_PASSWORD"),
            ssl=True,
            decode_responses=True
        )

    def create_job(self, job_id: str, initial_data: dict, ttl_seconds: int = REDIS_STORE_TIME):
        self.client.setex(job_id, ttl_seconds, json.dumps(initial_data))

    def update_job(self, job_id: str, key: str, value: Any):
        job = self.get_job(job_id)
        if job:
            job[key] = value
            self.client.set(job_id, json.dumps(job))

    def get_job(self, job_id: str) -> Optional[dict]:
        data = self.client.get(job_id)
        return json.loads(data) if data else None

    def delete_job(self, job_id: str):
        self.client.delete(job_id)

    def get_all_jobs(self) -> dict:
        keys = self.client.keys("*")
        result = {}
        for key in keys:
            data = self.client.get(key)
            if data:
                result[key] = json.loads(data)
        return result
    
job_store = JobStoreManager()