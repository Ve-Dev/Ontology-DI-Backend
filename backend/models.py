# Create your models here.

from django.db import models

class File(models.Model):

    originalFile1 = models.FileField()
    originalFile2 = models.FileField()
    csvFile = models.FileField()
    rdfFile = models.FileField()
    jsonFile = models.FileField(null=True)

    def __str__(self):
        # return self.pdf
        #if (self.rdfFile.name == ""):
        #    return self.originalFile1.name
        return str(self.id)
    
