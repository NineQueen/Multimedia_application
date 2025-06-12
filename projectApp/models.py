from django.db import models

# Create your models here.
# 接受信息并存储到数据库中
class Information(models.Model):
    node_id = models.CharField(max_length=4)
    loc = models.CharField(max_length=6)
    temp = models.DecimalField(max_digits=5,decimal_places=1)
    hum = models.DecimalField(max_digits=5,decimal_places=1)
    light = models.IntegerField()
    snd = models.IntegerField()
    date_created = models.DateTimeField(auto_now_add=True)
    
    def __str__(self) -> str:
        return "Information #{}".format(self.id)
    
    class Meta:
        verbose_name_plural = "Information"

class WarningMessage(models.Model):
    information = models.OneToOneField(
        Information,
        on_delete=models.CASCADE,
        related_name="warning",
        verbose_name="warning"
    )
    message = models.TextField(blank=True,null=True)
    def __str__(self) -> str:
        return "WarningMessage #{}".format(self.id)
    class Meta:
        verbose_name_plural = "WarningMessage"

class Warning(models.Model):
    message = models.ManyToManyField(
        WarningMessage,
        blank= True
    )
    loc = models.CharField(max_length=6)
    date_created = models.DateTimeField(auto_now_add=True)
    status = models.BooleanField(default=False)


class Event(models.Model):
    name = models.CharField(max_length=10)
    begin_time = models.DateTimeField()
    end_time = models.DateTimeField()
    loc = models.CharField(max_length=20)
    Description = models.TextField(null=True,blank=True)
    instructor = models.CharField(max_length=20,null=False)
    def __str__(self):
        return "Event #{}".format(self.id)
    
    class Meta:
        verbose_name_plural = "Events"