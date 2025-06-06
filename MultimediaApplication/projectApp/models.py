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