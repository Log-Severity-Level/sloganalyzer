from django.forms import ModelForm
from core.models import CompareBranch
from django.core.exceptions import ValidationError

# Create the form class.
class CompareBranchForm(ModelForm):
    class Meta:
        model = CompareBranch
        fields = ['system', 'branch_initial', 'branch_final', ]
        
    def clean(self):
        cleaned_data = super().clean()
        system = cleaned_data.get("system")
        branch_initial = cleaned_data.get("branch_initial")
        branch_final = cleaned_data.get("branch_final")

        if branch_initial.system !=  branch_final.system or branch_initial.system !=  system:
            raise ValidationError(
                    "The branches must belong to the source system." )

        if branch_initial ==  branch_final:
            raise ValidationError(
                    "The branches must be different." )
