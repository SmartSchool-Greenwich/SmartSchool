from django.db import models
from django.contrib.auth.models import User


class Role(models.Model):
    name = models.CharField(max_length=30)
    
    def __str__(self):
        return self.name
    
    def get_marketing_coordinator_role():
        return Role.objects.filter(name='marketing cordinator').first()

    @classmethod
    def create_default_role(cls):
        default_role, created = cls.objects.get_or_create(name='student')
        return default_role
    
    @classmethod
    def get_or_create_guest_role(cls):
        guest_role, created = cls.objects.get_or_create(name='guest')
        return guest_role


class AcademicYear(models.Model):
    closure = models.DateTimeField()
    finalClosure = models.DateTimeField()
    code = models.CharField(max_length = 6, blank=True)

    def __str__(self):
        closure_date = self.closure.strftime('%Y-%m-%d')
        return f'Closure Date: {closure_date}'
    
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    fullname = models.CharField(max_length=50)
    roles = models.ManyToManyField(Role, related_name='users')
    
    faculty = models.ForeignKey('Faculties', on_delete=models.CASCADE, null=True, blank=True)
    
    email = models.EmailField(max_length=254, unique=True, blank=True, null=True)
    phone = models.CharField(max_length=15)
    
    academic_Year = models.ForeignKey(AcademicYear,blank=True, null =True, on_delete=models.CASCADE)
    

    def __str__(self):
        return self.fullname

    def save(self, *args, **kwargs):
        super(UserProfile, self).save(*args, **kwargs)  
        if not self.roles.exists():  
            if self.faculty is None:
                guest_role = Role.get_or_create_guest_role()
                self.roles.add(guest_role)
            else:
                default_role = Role.create_default_role()
                self.roles.add(default_role)

class Faculties(models.Model):
    name = models.CharField(max_length = 40)
    description = models.TextField(null =True)
    def __str__(self):
        return self.name
    


class Contributions(models.Model):
    user = models.ManyToManyField(UserProfile)
    title = models.CharField(max_length=30)
    content = models.TextField(null = True)
    faculty = models.ForeignKey(Faculties,on_delete=models.CASCADE)
    term = models.BooleanField(default=False)
    createAt = models.DateTimeField(auto_now_add=True)
    academic_Year = models.ForeignKey(AcademicYear,blank=True, null =True, on_delete=models.CASCADE)
    reject_reason = models.TextField(blank=True, null=True) 
    status = models.CharField(max_length=10,  default='waiting')
    public = models.BooleanField(default = False)
    def __str__(self):
        return self.title


class ContributionFiles(models.Model):
    word = models.FileField(null = True)
    img = models.FileField(null = True)
    contribution = models.ForeignKey(Contributions, on_delete=models.CASCADE, related_name='files', null=True)
    
    def __str__(self):
        return self.contribution.title if self.contribution else 'No Contribution'


class Comment(models.Model):
    user = models.ForeignKey(UserProfile,on_delete = models.CASCADE)
    contribution = models.ForeignKey(Contributions,on_delete = models.CASCADE)
    comment = models.TextField(blank=True,null=True)
    createAt = models.DateTimeField(auto_now_add=True)

    def __str__ (self):
        return f"{self.user.user.username} comment on {self.contribution}"

