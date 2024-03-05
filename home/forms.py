from django import forms

from home.models import ContributionFiles,UserProfile,User,Role,Contributions

class ContributionFileForm(forms.ModelForm):
    class Meta:
        model = ContributionFiles
        fields = ('word', 'img',)

    def clean(self):
        cleaned_data = super().clean()
        word = cleaned_data.get('word')
        img = cleaned_data.get('img')

        # Check if neither field has a file uploaded.
        if not word and not img:
            raise forms.ValidationError("You must upload either a Word document or an image.")

        return cleaned_data
    def __init__(self, *args, **kwargs):
        super(ContributionFileForm, self).__init__(*args, **kwargs)
        self.fields['img'].required = False
        self.fields['word'].required = False


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)
    role = forms.ModelChoiceField(queryset=Role.objects.exclude(name='student'), empty_label="Select Role")

    class Meta:
        model = User
        fields = ('username', 'password')

    def clean_confirm_password(self):
        cd = self.cleaned_data
        if cd['password'] != cd['confirm_password']:
            raise forms.ValidationError('Passwords don\'t match.')
        return cd['confirm_password']

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('fullname', 'phone',)



class ContributionForm(forms.ModelForm):
    class Meta:
        model = Contributions
        fields = ('title', 'content', 'status', 'term', 'faculty')
