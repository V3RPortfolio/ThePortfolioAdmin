from django.db import models
from datetime import datetime

# Create your models here.
class PostSynchronizationProgress(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_COMPLETED = 'completed'
    STATUS_FAILED = 'failed'
    TOTAL_UPDATE_STEPS = 10

    id = models.AutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    progress = models.IntegerField(default=0)
    status = models.CharField(max_length=20, default='pending')
    message = models.TextField(default='', max_length=200)

    def __str__(self):
        return f'{self.progress}/{self.total} - {self.status}'

    
    def _update_status(self, status:str, message:str, current_step:int=1):
        self.updated_at = datetime.now()
        self.status = status
        self.message = message

        if status == self.STATUS_FAILED or status == self.STATUS_COMPLETED:
            current_step = -1

        if current_step < 0 or current_step > self.TOTAL_UPDATE_STEPS:
            self.progress = 100
        else:
            self.progress = current_step / self.TOTAL_UPDATE_STEPS * 100

        print(f"Task: {self.id} - Progress: {self.progress} - Status: {self.status} - Message: {self.message}")

    def update_progress(self, status:str, message:str, current_step:int=1):
        self._update_status(status, message, current_step)
        self.save()

    async def aupdate_progress(self, status:str, message:str, current_step:int=1):
        self._update_status(status, message, current_step)
        await self.asave()

    
    class Meta:
        ordering = ['created_at']
        verbose_name = 'Post Synchronization Progress'
        verbose_name_plural = 'Post Synchronization Progress'