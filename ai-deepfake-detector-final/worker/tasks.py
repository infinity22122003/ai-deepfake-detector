
from celery import Celery
import random

celery = Celery("tasks", broker="redis://redis:6379/0")

@celery.task(name="tasks.analyze")
def analyze(case_id):
    verdict = random.choice(["real","fake"])
    return verdict
