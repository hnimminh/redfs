import gevent
import redfs
import traceback


ESL_HOST = '127.0.0.1'
ESL_PORT = 8021
ESL_PASSWORD = 'your-esl-password'
ESL_TIMEOUT = 10


def dosome(event):
    event_name = event.headers.get('Event-Name')
    uuid = event.headers.get('Unique-ID')
    print(f'Event {event_name} with uuid {uuid}')

    conn = redfs.InboundESL(host=ESL_HOST, port=ESL_PORT, password=ESL_PASSWORD, timeout=ESL_TIMEOUT)
    conn.connect()

    if event_name == 'CHANNEL_PARK':
        cmd = f'api uuid_answer {uuid}'
        res = conn.send(cmd)
        print(cmd, res.data)


cnx = redfs.InboundESL(host=ESL_HOST, port=ESL_PORT, password=ESL_PASSWORD, timeout=ESL_TIMEOUT)
cnx.connect()
cnx.register_handle('*', dosome)
cnx.send('EVENTS PLAIN ALL')
print('connected')
while True:
    try:
        gevent.sleep(1)
    except KeyboardInterrupt:
        cnx.stop()
        break
    except Exception as e:
        print(e, traceback.format_exc())