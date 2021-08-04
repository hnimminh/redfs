#!/usr/bin/env python

import logging
import pprint

import gevent
import gevent.socket as socket
from gevent.event import Event
from gevent.queue import Queue
from urllib.parse import unquote


class NotConnectedError(Exception):
    pass

class ESLEvent(object):
    def __init__(self, data):
        self.headers = {}
        self.parse_data(data)

    def parse_data(self, data):
        data = unquote(data)
        data = data.strip().splitlines()
        last_key = None
        value = ''
        for line in data:
            if ': ' in line:
                key, value = line.split(': ', 1)
                last_key = key
            else:
                key = last_key
                value += '\n' + line
            self.headers[key.strip()] = value.strip()


class ESLProtocol(object):
    def __init__(self):
        self._run = True
        self._EOL = '\n'
        self._commands_sent = []
        self._auth_request_event = Event()
        self._receive_events_greenlet = None
        self._process_events_greenlet = None
        self.event_handlers = {}
        self._esl_event_queue = Queue()
        self._process_esl_event_queue = True
        self._lingering = False
        self.connected = False

    def start_event_handlers(self):
        self._receive_events_greenlet = gevent.spawn(self.receive_events)
        self._process_events_greenlet = gevent.spawn(self.process_events)

    def register_handle(self, names, handler):
        for name in names:
            if name not in self.event_handlers:
                self.event_handlers[name] = []
            if handler in self.event_handlers[name]:
                return
            self.event_handlers[name].append(handler)

    def unregister_handle(self, name, handler):
        if name not in self.event_handlers:
            raise ValueError(f'No handlers found for event: {name}')
        self.event_handlers[name].remove(handler)
        if not self.event_handlers[name]:
            del self.event_handlers[name]

    def receive_events(self):
        buf = ''
        while self._run:
            try:
                data = self.sock_file.readline()
            except Exception:
                self._run = False
                self.connected = False
                self.sock.close()
                # logging.exception("Error reading from socket.")
                break

            if not data:
                if self.connected:
                    logging.error("Error receiving data, is FreeSWITCH running?")
                    self.connected = False
                    self._run = False
                break
            # Empty line
            if data == self._EOL:
                event = ESLEvent(buf)
                buf = ''
                self.handle_event(event)
                continue
            buf += data

    @staticmethod
    def _read_socket(sock, length):
        """Receive data from socket until the length is reached."""
        data = sock.read(length)
        data_length = len(data)
        while data_length < length:
            logging.warn(f'Socket should read {length} bytes, but actually read {data_length} bytes. '
                          'Consider increasing "net.core.rmem_default".')
            # FIXME: if not data raise error
            data += sock.read(length - data_length)
            data_length = len(data)
        return data

    def handle_event(self, event):
        if event.headers['Content-Type'] == 'auth/request':
            self._auth_request_event.set()
        elif event.headers['Content-Type'] == 'command/reply':
            async_response = self._commands_sent.pop(0)
            event.data = event.headers['Reply-Text']
            async_response.set(event)
        elif event.headers['Content-Type'] == 'api/response':
            length = int(event.headers['Content-Length'])
            data = self._read_socket(self.sock_file, length)
            event.data = data
            async_response = self._commands_sent.pop(0)
            async_response.set(event)
        elif event.headers['Content-Type'] == 'text/disconnect-notice':
            if event.headers.get('Content-Disposition') == 'linger':
                logging.debug('Linger activated')
                self._lingering = True
            else:
                self.connected = False
            # disconnect-notice is now a propagated event both for inbound
            # and outbound socket modes.
            # This is useful for outbound mode to notify all remaining
            # waiting commands to stop blocking and send a NotConnectedError
            self._esl_event_queue.put(event)
        elif event.headers['Content-Type'] == 'text/rude-rejection':
            self.connected = False
            length = int(event.headers['Content-Length'])
            self._read_socket(self.sock_file, length)
            self._auth_request_event.set()
        else:
            length = int(event.headers['Content-Length'])
            data = self._read_socket(self.sock_file, length)
            if event.headers.get('Content-Type') == 'log/data':
                event.data = data
            else:
                event.parse_data(data)
            self._esl_event_queue.put(event)

    def _safe_exec_handler(self, handler, event):
        try:
            handler(event)
        except:
            logging.exception(f'ESL {handler.__name__} raised exception.')
            logging.error(pprint.pformat(event.headers))

    def process_events(self):
        logging.debug('Event Processor Running')
        while self._run:
            if not self._process_esl_event_queue:
                gevent.sleep(1)
                continue

            try:
                event = self._esl_event_queue.get(timeout=1)
            except gevent.queue.Empty:
                continue

            if event.headers.get('Event-Name') == 'CUSTOM':
                handlers = self.event_handlers.get(event.headers.get('Event-Subclass'))
            else:
                handlers = self.event_handlers.get(event.headers.get('Event-Name'))

            if event.headers.get('Content-Type') == 'text/disconnect-notice':
                handlers = self.event_handlers.get('DISCONNECT')

            if not handlers and event.headers.get('Content-Type') == 'log/data':
                handlers = self.event_handlers.get('log')

            if not handlers and '*' in self.event_handlers:
                handlers = self.event_handlers.get('*')

            if not handlers:
                continue

            if hasattr(self, 'before_handle'):
                self._safe_exec_handler(self.before_handle, event)

            for handle in handlers:
                self._safe_exec_handler(handle, event)

            if hasattr(self, 'after_handle'):
                self._safe_exec_handler(self.after_handle, event)

    def send(self, data):
        if not self.connected:
            raise NotConnectedError()
        async_response = gevent.event.AsyncResult()
        self._commands_sent.append(async_response)
        raw_msg = (data + self._EOL*2).encode('utf-8')
        self.sock.send(raw_msg)
        response = async_response.get()
        return response

    def stop(self):
        if self.connected:
            try:
                self.send('exit')
            except (NotConnectedError, socket.error):
                pass
        self._run = False
        if self._receive_events_greenlet:
            logging.info("Waiting for receive greenlet exit")
            self._receive_events_greenlet.join()
        if self._process_events_greenlet:
            logging.info("Waiting for event processing greenlet exit")
            self._process_events_greenlet.join()
        self.sock.close()
        self.sock_file.close()


class InboundESL(ESLProtocol):
    def __init__(self, host, port, password, timeout=5):
        super(InboundESL, self).__init__()
        self.host = host
        self.port = port
        self.password = password
        self.timeout = timeout
        self.connected = False

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        try:
            self.sock.connect((self.host, self.port))
        except socket.timeout:
            raise NotConnectedError(f'Connection timed out after {self.timeout} seconds')

        self.connected = True
        self.sock.settimeout(None)
        self.sock_file = self.sock.makefile()
        self.start_event_handlers()
        self._auth_request_event.wait()
        if not self.connected:
            raise NotConnectedError('Server closed connection, check FreeSWITCH config.')
        self.authenticate()

    def authenticate(self):
        response = self.send(f'auth {self.password}')
        if response.headers['Reply-Text'] != '+OK accepted':
            raise ValueError('Invalid password.')

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
