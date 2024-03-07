from django.contrib import admin

from .models import UserProfile,ContributionFiles,Contributions,Faculties,Role,AcademicYear,Comment

admin.site.register(UserProfile)
admin.site.register(ContributionFiles)
admin.site.register(Contributions)
admin.site.register(Faculties)
admin.site.register(Role)
admin.site.register(AcademicYear)
admin.site.register(Comment)




