<p align="center">
  <img width="128" src="https://user-images.githubusercontent.com/58973699/125749787-cc7844b2-aea4-4c98-8efd-c413f6aec317.png">  
</p>

<p align="center">
  <br>
  <strong>RedFS - FreeSWITCH Event Socket </strong>
  <br>
  <code>FreeSWITCH Event Socket Protocol Client Library by Python3:Genvet</code>
  <br><br>
</p>


## Why RedFS ?
It's origin fork from greenswitch, with some adapt implementation for:
* Minimalize dependency (gevent only)
* Python3 syntax improvement
* Large scale adaptation


## Usage

**Installation**
```bash
pip3 install redfs
```

**Example**

```python
    >>> import redfs
    >>> fs = redfs.InboundESL(host='127.0.0.1', port=8021, password='ClueCon')
    >>> fs.connect()
    >>> r = fs.send('api list_users')
    >>> print r.data
```

Enjoy!

## License
[MIT](./LICENSE)