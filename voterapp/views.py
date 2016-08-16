from django.http import HttpResponse
from django.shortcuts import render
from Voter.settings import CONFIG
import os
import base64
import psycopg2
import scrypt
import json


def index(request):
    maxcandidates = 20
    context = {
        'candidates': {},
        'range': range(1, maxcandidates + 1),
        'maxCandidates': maxcandidates
    }
    connection = getconnection()
    cursor = connection.cursor()
    cursor.execute("SELECT name,id FROM candidates")
    results = cursor.fetchmany(100)
    for result in results:
        context['candidates'][result[0]] = result[1]
    return render(request=request, context=context, template_name='voterapp/vote.html')


def hashemail(email):
    config = CONFIG['emailHashing']
    N = 2**(int(config['N']))
    r = int(config['r'])
    p = int(config['p'])
    buflen = int(config['buflen'])
    return base64.b64encode(scrypt.hash(email,
                                        CONFIG['emailHashing']['salt'], N=N, r=r, p=p, buflen=buflen),
                            b'+_').decode('utf-8')


def getconnection():
    config = CONFIG['database']
    host = config['host']
    database = config['database']
    user = config['user']
    password = config['password']
    port = config['port']
    connection = psycopg2.connect(host=host, port=port, database=database, user=user, password=password)
    return connection


def submitvote(request):
    candidates = json.loads(request.POST['candidates'])
    # print(repr(candidates))
    email = request.POST['email']

    # print(voteID)
    query = ["INSERT INTO tentative_votes (id, email ", ") VALUES (%s, %s"]
    args = [None, hashemail(email)]
    for i in range(0, len(candidates)):
        query[0] += ', c' + str(i + 1)
        query[1] += ', %s'
        args.append(candidates[i])
    query = query[0] + query[1] + ");"
    failurecount = 0
    with getconnection() as connection:
        with connection.cursor() as cursor:
            success = False
            failurecount = 0
            while (not success) and (failurecount < 5):
                print("Try number " + str(failurecount))
                try:
                    voteid = base64.b64encode(os.urandom(24), b'+_').decode('utf-8')
                    args[0] = voteid
                    cursor.execute(query, args)
                    success = True
                except psycopg2.IntegrityError:
                    failurecount += 1
                    connection.rollback()

            if not success:
                print("Wtf happened?")
                return HttpResponse(status=500)

    return HttpResponse("Much success after " + str(failurecount) + " tries")
