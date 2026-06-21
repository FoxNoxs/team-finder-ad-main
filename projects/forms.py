from django import forms

from .models import Project


class ProjectForm(forms.ModelForm):
    """Форма создания и редактирования проекта."""

    class Meta:
        model = Project
        fields = ['name', 'description', 'github_url', 'status']
        widgets = {
            'status': forms.Select(choices=[
                ('open', 'Открыт'),
                ('closed', 'Закрыт'),
            ]),
        }

    def clean_github_url(self):
        url = self.cleaned_data.get('github_url', '').strip()
        if not url:
            return url
        if not url.startswith(('http://github.com', 'https://github.com',
                               'http://www.github.com', 'https://www.github.com')):
            raise forms.ValidationError('Ссылка должна вести на GitHub.')
        return url
