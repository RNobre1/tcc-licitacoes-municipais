from django.db import models


class RawRecord(models.Model):
    endpoint = models.TextField()
    params = models.JSONField(default=dict, blank=True)
    fetched_at = models.DateTimeField()
    payload = models.JSONField()
    status_code = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.endpoint} at {self.fetched_at}"
