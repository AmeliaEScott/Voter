from django.http import HttpResponse
from django.shortcuts import render
import psycopg2


def index(request):
    maxcandidates = 20
    context = {
        'candidates': [],
        'range': range(1, maxcandidates + 1),
        'maxCandidates': maxcandidates
    }
    connection = psycopg2.connect(host='localhost', database='votes', user='timmy')
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM candidates")
    results = cursor.fetchmany(100)
    for result in results:
        context['candidates'].append(result[1])
    return render(request=request, context=context, template_name='voterapp/vote.html')


def submitvote(request):
    print(repr(request.POST['candidates']))
    return HttpResponse("Much success")
