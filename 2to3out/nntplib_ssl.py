import nntplib
import re
import socket            
new_ssl_loaded = False
try:
    import ssl
    new_ssl_loaded = True
except Exception as e:
    pass

NNTP_SSL_PORT = 563
CRLF = '\r\n'

class error_proto(Exception):
    pass

class NNTP_SSL(nntplib.NNTP):
    """NNTP client class over SSL connection

    Instantiate with: NNTP_SSL(hostname, port=NNTP_SSL_PORT, user=None,
	                             password=None, readermode=None, usenetrc=True,
                               keyfile=None, certfile=None)

        - host: hostname to connect to
        - port: port to connect to (default the standard NNTP port)
        - user: username to authenticate with
        - password: password to use with username
        - readermode: if true, send 'mode reader' command after
                      connecting.
        - keyfile: PEM formatted file that contains your private key
        - certfile: PEM formatted certificate chain file

        See the methods of the parent class NNTP for more documentation.
    """

    def __init__(self, host, port = NNTP_SSL_PORT, user=None, password=None,
                 readermode=None, usenetrc=True,
                 keyfile = None, certfile = None):
        self.host = host
        self.port = port
        self.keyfile = keyfile
        self.certfile = certfile
        self.buffer = ""
        msg = "getaddrinfo returns an empty list"
        self.sock = None
        for res in socket.getaddrinfo(self.host, self.port, 0, socket.SOCK_STREAM):
            af, socktype, proto, canonname, sa = res
            try:
                self.sock = socket.socket(af, socktype, proto)
                self.sock.connect(sa)
            except socket.error as msg:
                if self.sock:
                    self.sock.close()
                self.sock = None
                continue
            break
        if not self.sock:
            raise socket.error(msg)
        self.file = self.sock.makefile('rb')
        if new_ssl_loaded:
            self.sslobj = ssl.wrap_socket(self.sock, self.keyfile, self.certfile)
        else:
            self.sslobj = socket.ssl(self.sock, self.keyfile, self.certfile)
        self.debugging = 0
        self.welcome = self.getresp()

        # 'mode reader' is sometimes necessary to enable 'reader' mode.
        # However, the order in which 'mode reader' and 'authinfo' need to
        # arrive differs between some NNTP servers. Try to send
        # 'mode reader', and if it fails with an authorization failed
        # error, try again after sending authinfo.
        readermode_afterauth = 0
        if readermode:
            try:
                self.welcome = self.shortcmd('mode reader')
            except NNTPPermanentError:
                # error 500, probably 'not implemented'
                pass
            except NNTPTemporaryError as e:
                if user and e.response[:3] == '480':
                    # Need authorization before 'mode reader'
                    readermode_afterauth = 1
                else:
                    raise
        # If no login/password was specified, try to get them from ~/.netrc
        # Presume that if .netc has an entry, NNRP authentication is required.
        try:
            if usenetrc and not user:
                import netrc
                credentials = netrc.netrc()
                auth = credentials.authenticators(host)
                if auth:
                    user = auth[0]
                    password = auth[2]
        except IOError:
            pass
        # Perform NNRP authentication if needed.
        if user:
            resp = self.shortcmd('authinfo user '+user)
            if resp[:3] == '381':
                if not password:
                    raise NNTPReplyError(resp)
                else:
                    resp = self.shortcmd(
                            'authinfo pass '+password)
                    if resp[:3] != '281':
                        raise NNTPPermanentError(resp)
            if readermode_afterauth:
                try:
                    self.welcome = self.shortcmd('mode reader')
                except NNTPPermanentError:
                    # error 500, probably 'not implemented'
                    pass

    def _fillBuffer(self):
        localbuf = self.sslobj.read()
        if len(localbuf) == 0:
            raise error_proto('-ERR EOF')
        self.buffer += localbuf

    def getline(self):
        line = ""
        renewline = re.compile(r'.*?\n')
        match = renewline.match(self.buffer)
        while not match:
            self._fillBuffer()
            match = renewline.match(self.buffer)
        line = match.group(0)
        self.buffer = renewline.sub('' ,self.buffer, 1)
        if self.debugging > 1: print('*get*', repr(line))

        if not line: raise EOFError
        if line[-2:] == CRLF: line = line[:-2]
        elif line[-1:] in CRLF: line = line[:-1]
        return line

    def putline(self, line):
        if self.debugging > 1: print('*put*', repr(line))
        line += CRLF
        bytes = len(line)
        while bytes > 0:
            sent = self.sslobj.write(line)
            if sent == bytes:
                break    # avoid copy
            line = line[sent:]
            bytes = bytes - sent

    def quit(self):
        """Process a QUIT command and close the socket.  Returns:
        - resp: server response if successful"""
        try:
            resp = self.shortcmd('QUIT')
        except error_proto as val:
            resp = str(val)
        self.sock.close()
        del self.sslobj, self.sock
        return resp
