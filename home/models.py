from django.db import models
from django.contrib.auth.models import User

class Role(models.Model):
    name = models.CharField(max_length=20)

    @classmethod
    def create_default_role(cls):
        default_role, created = cls.objects.get_or_create(name='user')
        return default_role

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    fullname = models.CharField(max_length=50)
    roles = models.ManyToManyField(Role, related_name='users')
    email = models.EmailField(max_length=254, unique=True)
    phone = models.CharField(max_length=15)

    def __str__(self):
        return self.fullname

    def save(self, *args, **kwargs):
        if not self.pk:
            default_role = Role.create_default_role()
            self.roles.add(default_role)
        super(UserProfile, self).save(*args, **kwargs)
