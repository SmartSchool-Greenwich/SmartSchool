from django.contrib import admin

from .models import UserProfile,ContributionFiles,Contributions,Faculties,Role

admin.site.register(UserProfile)
admin.site.register(ContributionFiles)
admin.site.register(Contributions)
admin.site.register(Faculties)
admin.site.register(Role)


