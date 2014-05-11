#!/usr/bin/env python3.4
#
# Copyright (c) 2013-2014 by Ron Frederick <ronf@timeheart.net>.
# All rights reserved.
#
# This program and the accompanying materials are made available under
# the terms of the Eclipse Public License v1.0 which accompanies this
# distribution and is available at:
#
#     http://www.eclipse.org/legal/epl-v10.html
#
# Contributors:
#     Ron Frederick - initial implementation, API, and documentation

import asyncio, asyncssh, crypt, sys

# To run this program, the file ssh_host_keys must exist with at least
# one SSH private key to use as a server host key in it
ssh_host_keys = asyncssh.read_private_key_list('ssh_host_keys')

class MySSHServerSession(asyncssh.SSHServerSession):
    def __init__(self):
        self._input = ''
        self._total = 0

    def connection_made(self, chan):
        self._chan = chan

    def shell_requested(self):
        return True

    def data_received(self, data, datatype):
        self._input += data

        lines = self._input.split('\n')
        for line in lines[:-1]:
            try:
                if line:
                    self._total += int(line)
            except ValueError:
                self._chan.write('Invalid number: %s\r\n' % line)

        self._input = lines[-1]

    def eof_received(self):
        self._chan.write('Total = %s\r\n' % self._total)
        self._chan.close()

class MySSHServer(asyncssh.SSHServer):
    def connection_made(self, conn):
        self._conn = conn

    def connection_lost(self, exc):
        if exc:
            print('SSH connection error: ' + str(exc), file=sys.stderr)

    def begin_auth(self, username):
        # No auth in this example
        return False

    @asyncio.coroutine
    def session_requested(self):
        return MySSHServerSession()

@asyncio.coroutine
def start_server():
    yield from asyncssh.create_server(MySSHServer, 'localhost', 8022,
                                      server_host_keys=ssh_host_keys)

loop = asyncio.get_event_loop()

try:
    loop.run_until_complete(start_server())
except (OSError, asyncssh.Error) as exc:
    sys.exit('Error starting server: ' + str(exc))

loop.run_forever()
