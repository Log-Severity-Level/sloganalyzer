import json

from django.http import HttpResponse
from django.shortcuts import render

from core.models import *


def dashboard_with_pivot(request):
    return render(request, 'dashboard_with_pivot.html', {})

def pivot_data(request):
    branchs = Branch.objects.all()
    dataset = []
    for branch in branchs:
        dataset.append({
            "model": "core.branch",
            "pk": branch.id,
            "fields": {
                'system': branch.system.name,
                'branch': branch.name,
                'version': f"{branch.system.name}/{branch.std_version}",
                'log_statement_number': branch.log_statement_number,
                'file_number': branch.file_number,
                'method_number': branch.method_number,
                'nloc': branch.nloc,
                'cyclomatic_complexity': branch.cyclomatic_complexity,
            }
        })
    return HttpResponse(str(json.dumps(dataset)))