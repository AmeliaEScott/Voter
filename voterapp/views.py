from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseServerError, HttpResponseNotFound
from django.shortcuts import render
from django.utils.datastructures import MultiValueDictKeyError
from django.core import mail
import smtplib
from Voter.settings import CONFIG, BASE_DIR
import os
import random
import base64
import psycopg2
from psycopg2 import pool
import scrypt
import json
import re
import atexit

config = CONFIG['database']
host = config['host']
database = config['database']
user = config['user']
password = config['password']
port = config['port']
connectionPool = pool.ThreadedConnectionPool(5, 10,
                                             host=host, port=port, database=database, user=user, password=password)
maxcandidates = 20
regex = re.compile(r'^(([^<>()[\]\\.,;:\s@\"]+(\.[^<>()[\]\\.,;:\s@\"]+)*)|(\".+\"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.'
                   '[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$')
mailConnection = mail.get_connection(**(CONFIG['email']['send']))
# mailConnection.open()

with open(os.path.join(BASE_DIR, 'hitcounts.json')) as file:
    hitCounts = json.load(file)


def savehitcounts():
    with open(os.path.join(BASE_DIR, 'hitcounts.json'), 'w+') as file:
        file.truncate()
        json.dump(hitCounts, file)
    print("Hitcount file saved")

atexit.register(savehitcounts)


def index(request):
    hitCounts['index'] += 1
    return HttpResponse(render(request=request, template_name='voterapp/index.html'))


def faq(request):
    return HttpResponse(render(request=request, template_name='voterapp/faq.html'))


def vote(request):
    context = {
        'candidates': {},
        'range': range(1, maxcandidates + 1),
        'maxCandidates': maxcandidates,
        'ballot': []
    }
    with ConnectionWrapper(connectionPool) as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT name,id,on_ballot FROM candidates ORDER BY name LIMIT 10000;")
        results = cursor.fetchmany(100)
        for result in results:
            context['candidates'][result[0]] = result[1]
            if result[2]:
                context['ballot'].append(result[0])
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

        candidate['oldname'] = candidate['name']
        candidate['name'] = re.sub(r"[^a-zA-Z' ]", string=candidate['name'], repl="")

        # This query returns the closest existing name and id, or makes a new candidate if
        # no existing candidates are close enough
        cursor.execute("SELECT id,resultName,isNew FROM add_candidate(%s)",
                       (candidate['name'].title(),))
        result = cursor.fetchmany(1)[0]

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
    try:
        candidates = json.loads(request.POST['candidates'])
        if len(candidates) > maxcandidates:
            context = {
                'error_message': str(len(candidates)) +
                ' candidates is too many. Limit yourself to ' + str(maxcandidates) + '.',
            }
            return HttpResponseBadRequest(render(request=request, template_name='voterapp/error.html', context=context))
    except ValueError:
        context = {
            'error_message': 'Badly formatted JSON for parameter "candidates": ' + request.POST['candidates'],
            'status': 400
        }
        return HttpResponseBadRequest(render(request=request, template_name='voterapp/error.html', context=context))
    except MultiValueDictKeyError:
        context = {
            'error_message': "Parameter 'candidates' not found.",
            'status': 400
        }
        return HttpResponseBadRequest(render(request=request, template_name='voterapp/error.html', context=context))
    # print(repr(candidates))
    emailaddress = request.POST['email']
    if regex.match(emailaddress) is None:
        context = {
            'error_message': '"' + emailaddress + '" is not a valid email address.',
            'status': 400
        }
        return HttpResponseBadRequest(render(request=request, template_name='voterapp/error.html', context=context))

    normalvote = {}
    try:
        normalvote = request.POST['normalvote']
        # print('Normalvote, unformatted: ' + normalvote)
        normalvote = json.loads(request.POST['normalvote'])
    except ValueError:
        context = {
            'error_message': 'Badly formatted JSON for parameter "normalvote": ' + request.POST['normalvote'],
            'status': 400
        }
        return HttpResponseBadRequest(render(request=request, template_name='voterapp/error.html', context=context))
    except MultiValueDictKeyError:
        pass

    # print('Normalvote: ' + repr(normalvote))

    emailhash = hashemail(emailaddress)

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
                    context = {
                        'error_message': 'You provided a candidate with no name or id. Original JSON: '
                                         + request.POST['candidates'],
                        'status': 400
                    }
                    return HttpResponseBadRequest(render(request=request, template_name='voterapp/error.html',
                                                         context=context))

                # Build up the query a little bit
                query[0] += ', c' + str(i + 1)
                query[1] += ', %s'

                if candidate['id'] in candidateids:
                    # Duplicate candidate
                    context = {
                        'error_message': 'Candidate number ' + str(candidate['id']) + ' was selected more than once.',
                        'status': 400
                    }
                    return HttpResponseBadRequest(render(request=request, template_name='voterapp/error.html',
                                                         context=context))
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
                context = {
                    'error_message': 'The email address you provided, "' + emailaddress + '", has already been'
                                     'used to cast a vote.',
                    'status': 400
                }
                return HttpResponseServerError(render(request=request, template_name='voterapp/error.html',
                                                      context=context))

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
                context = {
                    'error_message': 'Something has gone terribly wrong. '
                                     'Tell me if you see this message; I''ll know what it means.',
                    'status': 500
                }
                return HttpResponseServerError(render(request=request, template_name='voterapp/error.html',
                                                      context=context))
            else:
                # with  as emailConnection:
                try:
                    mailConnection.open()
                    message = "Thanks for voting! The last step is to click this link to confirm your vote.\n\n" \
                              "https://www.better-ballot.com/confirmvote/" + voteid + "/"
                    mail.EmailMessage(
                        "Vote confirmation", message, "noreply@better-ballot.com", (emailaddress, ),
                        connection=mailConnection,
                    ).send()
                    mailConnection.close()
                    connection.commit()
                    context = {
                        'candidates': candidates,
                        'email': emailaddress,
                        'normalvote': normalvote
                    }
                    hitCounts['votesCast'] += 1
                    return HttpResponse(render(request, 'voterapp/success.html', context=context))
                except smtplib.SMTPRecipientsRefused:
                    connection.rollback()
                    context = {
                        'error_message': 'Failed to send email to "' + emailaddress + '". Are you sure '
                                         'this is a valid address?',
                        'status': 400
                    }
                    return HttpResponseServerError(render(request=request, template_name='voterapp/error.html',
                                                   context=context))
                except:
                    connection.rollback()
                    context = {
                        'error_message': 'Something that I didn''t plan for has gone wrong. Please let me know '
                                         'about this error.',
                        'status': 500
                    }
                    return HttpResponseServerError(render(request=request, template_name='voterapp/error.html',
                                                   context=context))


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
                hitCounts['votesConfirmed'] += 1
                return HttpResponse(render(request=request, template_name='voterapp/confirmationSuccess.html'))
            else:
                connection.rollback()
                context = {
                    'error_message': 'The specified ID "' + voteid + '" was not found.',
                    'status': 404
                }
                return HttpResponseNotFound(render(request=request, template_name='voterapp/error.html',
                                                   context=context))


class ConnectionWrapper(object):

    def __init__(self, connpool):
        self.key = random.randint(1, 1000000)
        self.connpool = connpool

    def __enter__(self):
        self.connection = self.connpool.getconn(key=self.key)
        print("Got connection " + str(self.key))
        return self.connection

    def __exit__(self, *args):
        # if self.connection.status == psycopg2.extensions.STATUS_IN_TRANSACTION:
        # print("Rolling back connection")
        self.connection.rollback()
        self.connpool.putconn(self.connection, key=self.key)
        print("Put connection " + str(self.key))

    def getconnection(self):
        return self.connection
