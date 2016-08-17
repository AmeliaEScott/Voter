from django.http import HttpResponse
from django.shortcuts import render
from django.utils.datastructures import MultiValueDictKeyError
from Voter.settings import CONFIG
import os
import base64
import psycopg2
from psycopg2 import pool
import scrypt
import json
import re


config = CONFIG['database']
host = config['host']
database = config['database']
user = config['user']
password = config['password']
port = config['port']
connectionPool = pool.ThreadedConnectionPool(5, 30,
                                             host=host, port=port, database=database, user=user, password=password)
maxcandidates = 20
regex = re.compile(r'^(([^<>()[\]\\.,;:\s@\"]+(\.[^<>()[\]\\.,;:\s@\"]+)*)|(\".+\"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.'
                   '[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$')


def index(request):
    context = {
        'candidates': {},
        'range': range(1, maxcandidates + 1),
        'maxCandidates': maxcandidates
    }
    with ConnectionWrapper(connectionPool) as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT name,id FROM candidates")
        results = cursor.fetchmany(100)
        for result in results:
            context['candidates'][result[0]] = result[1]
        return render(request=request, context=context, template_name='voterapp/vote.html')


def hashemail(email):
    hashingconfig = CONFIG['emailHashing']
    n = 2**(int(hashingconfig['N']))
    r = int(hashingconfig['r'])
    p = int(hashingconfig['p'])
    buflen = int(hashingconfig['buflen'])
    return base64.b64encode(scrypt.hash(email,
                                        CONFIG['emailHashing']['salt'], N=n, r=r, p=p, buflen=buflen),
                            b'+_').decode('utf-8')


def fixcandidate(candidate, cursor):
    """
    Takes a candidate name and, if there's a close match in the database, returns their ID.
    If there's no close match, a new candidate is added to the database.

    :param candidate: Candidate dict that must contain at least 'name'
    :param cursor: For interacting with the database
    :return: The same candidate dict, with name corrected and/or id added,
             as well as 'corrected', 'isnew', and 'oldname'
    """
    if 'id' not in candidate:
        # If there's no 'name', then the user REALLY screwed up. Just give up.
        if 'name' not in candidate:
            return None

        # This query returns the closest existing name and id, or makes a new candidate if
        # no existing candidates are close enough
        cursor.execute("SELECT id,resultName,isNew FROM add_candidate(%s)",
                       (candidate['name'].title(),))
        result = cursor.fetchmany(1)[0]

        candidate['oldname'] = candidate['name']
        candidate['name'] = result[1]
        candidate['corrected'] = (candidate['name'].lower() != candidate['oldname'].lower())
        candidate['isnew'] = result[2]
        candidate['id'] = result[0]
        # print("Candidate not found: " + str(candidate['name']))
    else:
        candidate['isnew'] = False
        candidate['corrected'] = False
    return candidate


def submitvote(request):
    print(request.POST['candidates'])
    try:
        candidates = json.loads(request.POST['candidates'])
        if len(candidates) > maxcandidates:
            return HttpResponse('Too many candidates!', status=400)
    except ValueError:
        return HttpResponse('Badly formatted JSON: ' + request.POST['candidates'], status=400)
    except MultiValueDictKeyError:
        return HttpResponse(status=400)
    # print(repr(candidates))
    email = request.POST['email']
    if regex.match(email) is None:
        return HttpResponse('Poorly formatted email: ' + email, status=400)

    normalvote = {}
    try:
        normalvote = request.POST['normalvote']
        # print('Normalvote, unformatted: ' + normalvote)
        normalvote = json.loads(request.POST['normalvote'])
    except ValueError:
        return HttpResponse(status=400)
    except MultiValueDictKeyError:
        pass

    # print('Normalvote: ' + repr(normalvote))

    emailhash = hashemail(email)

    # print(voteID)

    with ConnectionWrapper(connectionPool) as connection:
        with connection.cursor() as cursor:
            query = ["INSERT INTO tentative_votes (id, email ", ") VALUES (%s, %s"]
            args = [None, emailhash]

            # This variable keeps track of the IDs of the candidates that have been successfully added to the query.
            # There is a problem where, if a user submits, for example, 'Bernie Sanders' and 'Bernie Sander', they'll
            # register as different candidates on the website, but the same candidate in the database.
            # This solves that problem.
            candidateids = []

            # Look through the candidates provided in the request
            for i in range(0, len(candidates)):
                candidate = fixcandidate(candidates[i], cursor)
                if candidate is None:
                    return HttpResponse(status=400)

                # Build up the query a little bit
                query[0] += ', c' + str(i + 1)
                query[1] += ', %s'

                if candidate['id'] in candidateids:
                    # Duplicate candidate
                    return HttpResponse(status=400)
                else:
                    args.append(candidate['id'])
                    candidateids.append(candidate['id'])

            normalvote = fixcandidate(normalvote, cursor)
            if normalvote is None:
                query = query[0] + query[1] + ");"
            else:
                query = query[0] + ", normalvote" + query[1] + ", %s);"
                args.append(normalvote['id'])

            cursor.execute("SELECT 1 FROM votes WHERE email=%s", (emailhash,))
            if len(cursor.fetchmany(1)) == 1:
                return HttpResponse("Email " + email + " already exists in database.", status=409)

            success = False
            failurecount = 0
            voteid = ''
            while (not success) and (failurecount < 5):
                print("Try number " + str(failurecount))
                try:
                    voteid = base64.b64encode(os.urandom(24), b'+_').decode('utf-8')
                    args[0] = voteid
                    cursor.execute(query, args)
                    connection.commit()
                    connectionPool.putconn(conn=connection, )
                    success = True
                except psycopg2.IntegrityError:
                    failurecount += 1
                    connection.rollback()

            if (not success) or voteid == '':
                print("Wtf happened?")
                connection.rollback()
                return HttpResponse(status=500)
            else:
                # TODO: Send email with link
                connection.commit()
                context = {
                    'candidates': candidates,
                    'email': email,
                    'normalvote': normalvote
                }
                return HttpResponse(render(request, 'voterapp/success.html', context=context))


def confirmvote(request, voteid):
    with ConnectionWrapper(connectionPool) as connection:
        with connection.cursor() as cursor:
            query = "INSERT INTO votes (email, created_at"
            for i in range(1, maxcandidates + 1):
                query += ', c' + str(i)
            query += ") SELECT email, created_at"
            for i in range(1, maxcandidates + 1):
                query += ', c' + str(i)
            query += ' FROM tentative_votes WHERE id=%s RETURNING email;'
            print(query)
            cursor.execute(query, (voteid, ))
            result = cursor.fetchmany(1)
            if len(result) == 1:
                email = result[0][0]
                print(email)
                cursor.execute("DELETE FROM tentative_votes WHERE email=%s;", (email, ))
                connection.commit()
                return HttpResponse("Such Success wow")
            else:
                connection.rollback()
                return HttpResponse(status=404)


class ConnectionWrapper(object):

    def __init__(self, connpool):
        self.connpool = connpool

    def __enter__(self):
        self.connection = self.connpool.getconn()
        return self.connpool.getconn()

    def __exit__(self, *args):
        self.connpool.putconn(self.connection)

    def getconnection(self):
        return self.connection
