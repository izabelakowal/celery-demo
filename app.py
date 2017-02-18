from flask import Flask, render_template
from celery import Celery, chain
from celery.result import AsyncResult
from celery.utils.log import get_task_logger
import logging
import time
import json
import os


app = Flask(__name__)
celery = Celery(
    'app',
    broker=os.environ['BROKER_URL'],
    backend='redis://localhost:6379/0'
)

#celery.config_from_object('celery_config')

'''
#  can also configure directly
celery = Celery(
    broker="amqp://guest@localhost//",
    backend="redis://localhost:6379/0"
)
'''


#  NORMAL LOGGING
handler = logging.StreamHandler()
app.logger.addHandler(handler)

#  CELERY LOGGING
celery_logger = get_task_logger(__name__)



###########
## TASKS ##
###########
@celery.task
def send_email(x, y):
   return x + y 


@celery.task
def add(n=100):
    celery_logger.info('I\'m in Celery!')
    i = 2
    result = []
    while i < n:
        flag = True
        for item in range(2, int(i**0.5)+1):
            if i % item == 0 and i != item: 
                flag = False
                break
        if flag:
            result.append(i)
        i += 1

        #  NOTE: this print statement will go to CELERY
        print result

    return result


############
## ROUTES ##
############
@app.route('/')
def index():
    '''Indx route.'''
    app.logger.info('I\'m Alive!')
    task = compute.delay(5)
    '''
    ^ We call our task asynchronously.
    Note that .delay is shorthand for .apply_async()
    This result is the task object,
    whose __repr__ is the task.id,
    which is available immediately,
    and is useful if we want to reference the task later,
    but is itself NOT the result of the function.
    '''
    

    #while not result.ready():
    #    #  NOTE: this print statement will go to STDOUT
    #    print('waiting.................')
    #    time.sleep(1)
    #result_final = result.get()
    '''
    ^ Here we wait until the task object .ready method
    returns True, and then we can ask for the function result.
    This blocks the page load though, which is not asynchronous.
    '''

    return render_template(
        'index.html',
        task=task,
    )


@app.route('/chaining/')
def chaining():
    '''Indx route.'''
    task_chain = chain(
        add.s(5, 7),         # First task
        add.s(10),           # Second task take result of first task and 10 as args
    )
    task = task_chain()
    raise Exception
    return render_template(
        'index.html',
        task=task,
    )


@app.route('/status/<task_id>/', methods=['GET'])
def taskstatus(task_id):
    """Get task status."""
    result = None
    
    task = compute.AsyncResult(task_id)
    '''
    ^ Get the task in it's present state.
    '''

    if task.ready():
        result = task.get()
    '''
    ^ If the task is done, we can ask for the result returned by our
    compute function.
    '''

    return json.dumps(
        {'state': task.state, 'result': result}
    )
    '''
    ^ We can respond to the request with a JSON object holding the taks state
    and the result of the function (if it exists).
    It's up to the client to determine what to do with that information.
    (e.g. ask again, render result etc.).
    '''