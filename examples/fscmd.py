import redfs
import traceback


ESL_HOST = '127.0.0.1'
ESL_PORT = 8021
ESL_PASSWORD = 'your-esl-password'
ESL_TIMEOUT = 10

try:
    conn = redfs.InboundESL(host=ESL_HOST, port=ESL_PORT, password=ESL_PASSWORD, timeout=ESL_TIMEOUT)
    conn.connect()
    cmd = f'api show codecs'
    res = conn.send(cmd)
    print(cmd, res.data)
    conn.stop()
except Exception as e:
    print(e, traceback.format_exc())