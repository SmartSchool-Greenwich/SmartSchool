from django import forms
from .models import Comment, ContributionFiles, Role

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['comment',]
class FileForm(forms.ModelForm):
    class Meta:
        model = ContributionFiles
        fields = ['word', 'img']          
        
class RoleForm(forms.ModelForm):
    class Meta:
        model = Role
        fields = ['name']

class RejectForm(forms.Form):
    reject_reason = forms.CharField(widget=forms.Textarea, label='Reason Reject')