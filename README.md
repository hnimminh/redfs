<p align="center">
  <img width="128" src="https://user-images.githubusercontent.com/58973699/125749787-cc7844b2-aea4-4c98-8efd-c413f6aec317.png">  
</p>

<p align="center">
  <a href="LICENSE.md" target="_blank">
    <img src="https://badgen.net/badge/license/MIT/blue" alt="">
  </a>
  <a href="https://github.com/hnimminh/redfs/releases" target="_blank">
    <img src="https://badgen.net/github/tag/hnimminh/redfs" alt="">
  </a>
  <a href="https://pypi.org/project/redfs" target="_blank">
    <img src="https://img.shields.io/pypi/pyversions/redfs" alt="">
  </a>
  <a href="https://pypi.org/project/redfs" target="_blank">
    <img src="https://img.shields.io/badge/download- xyz- red" alt="">
  </a>
</p>

<p align="center">
  <br>
  <strong>RedFS - FreeSWITCH Event Socket </strong>
  <br>
  <code>FreeSWITCH Event Socket Protocol Client Library by Python3:Gevent</code>
  <br><br>
</p>


## Why RedFS ?
It's origin fork from greenswitch, with some adapt implementation for:
* Minimalize dependency (gevent only)
* Python3 syntax improvement
* Large scale adaptation
* Bug fix


## Usage

**Installation**
```bash
pip3 install redfs
```

**FreeSWITCH configuration**

*event socket module*
```html
<configuration name="event_socket.conf" description="Socket Client">
  <settings>
    <param name="nat-map" value="false"/>
    <param name="listen-ip" value="127.0.0.1"/>
    <param name="listen-port" value="8021"/>
    <param name="password" value="your-esl-password"/>
  </settings>
</configuration>
```

*dialplan*
```html
<include>
  <context name="default">
    <extension name="daemon-ex">
      <condition regex="all">
        <regex field="destination_number" expression="."/>
        <action application="sched_hangup" data="+60 ALLOTTED_TIMEOUT"/>
        <action application="park"/>
        <anti-action application="hangup" data="REQUESTED_CHAN_UNAVAIL"/>
     </condition>
    </extension>
  </context>
</include>
```

a simple python application for auto answer.

```python
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
```

Enjoy!

## License
[MIT](./LICENSE)