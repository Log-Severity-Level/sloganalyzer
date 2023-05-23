from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

from core.models import *
import json


@login_required
def dashboard_cards(request):
    systems_count = System.objects.count()
    branches_count = Branch.objects.count()
    files_count = File.objects.count()
    severity_levels_count = SeverityLevel.objects.count()
    statements_count = Statement.objects.count()
    messages_count = Message.objects.count()
    context = {
        'systems_count': str(systems_count),
        'branches_count': str(branches_count),
        'files_count': str(files_count),
        'severity_levels_count': str(severity_levels_count),
        'statements_count': str(statements_count),
        'messages_count': str(messages_count),
    }
    return HttpResponse(json.dumps(context, indent=4))
