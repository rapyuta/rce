#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#     rce-core/rce/slave/interface.py
#
#     This file is part of the RoboEarth Cloud Engine framework.
#
#     This file was originally created for RoboEearth
#     http://www.roboearth.org/
#
#     The research leading to these results has received funding from
#     the European Union Seventh Framework Programme FP7/2007-2013 under
#     grant agreement no248942 RoboEarth.
#
#     Copyright 2013 RoboEarth
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
#
#     \author/s: Dominique Hunziker
#
#

# Python specific imports
from uuid import UUID

# twisted specific imports
from twisted.python import log
from twisted.spread.pb import Referenceable, \
    Error, DeadReferenceError, PBConnectionLost

# rce specific imports
from rce.util.error import InternalError


class Types(object):
    """ Available Interface types.
    """
    SERVICE_CLIENT = 0
    SERVICE_PROVIDER = 3
    PUBLISHER = 1
    SUBSCRIBER = 2
    _NAMES = ['ServiceClient', 'Publisher', 'Subscriber', 'ServiceProvider']

    @staticmethod
    def encode(typename):
        """ Encode an Interface type in string form as as an int.

            @param typename:    Interface type which should be encoded.
            @type  typename:    str

            @return:            Encoded Interface type.
            @rtype:             int
        """
        if typename.startswith(Types._NAMES[1]):
            return Types.PUBLISHER
        elif typename.startswith(Types._NAMES[2]):
            return Types.SUBSCRIBER
        elif typename.startswith(Types._NAMES[3]):
            return Types.SERVICE_PROVIDER
        elif typename.startswith(Types._NAMES[0]):
            return Types.SERVICE_CLIENT
        else:
            raise TypeError('Invalid interface type provided.')

    @staticmethod
    def decode(typenr):
        """ Decode an Interface type in int form as as a string.

            @param typenr:      Encoded Interface type which should be decoded.
            @type  typenr:      int

            @return:            Interface type.
            @rtype:             str
        """
        assert 0 <= typenr < 4
        return Types._NAMES[typenr]

    @staticmethod
    def connectable(iTypeA, iTypeB):
        """ Check if the two Interfaces are connectable.

            @param iTypeX:      Encoded Interface type.
            @type  iTypeX:      int

            @return:            True, if they are connectable; False otherwise.
            @rtype:             bool
        """
        return iTypeA + iTypeB == 3


class InvalidResoureName(Error):
    """ Exception is raised in case the interface resource name is invalid.
    """


class Interface(Referenceable):
    """ Abstract base class for an Interface in a slave process.
    """
    def __init__(self, owner, uid):
        """ Initialize the Interface.

            @param owner:       Namespace for which the Interface is created.
            @param owner:       rce.slave.namespace.Namespace

            @param uid:         Unique ID which is used to identify the
                                interface in the internal communication.
            @type  uid:         uuid.UUID
        """
        self._owner = owner
        owner.registerInterface(self)

        self._uid = uid
        self._protocols = {}

        self._ready = False

    @property
    def UID(self):
        """ Unique ID of the interface. """
        return self._uid

    def unregisterProtocol(self, protocol):
        """ Callback for the protocol to inform the interface that the
            protocol has died and should no longer be used.

            @param protocol:    Protocol which should be unregistered.
            @type  protocol:    rce.slave.protocol._Protocol
        """
        assert protocol in self._protocols
        del self._protocols[protocol]

        if not self._protocols:
            self.stop()

    def remote_connect(self, protocol, remoteID):
        """ Connect this interface to another interface using a local protocol.

            @param protocol:    Protocol instance which should be used to
                                establish the connection.
            @type  protocol:    rce.slave.protocol._Protocol

            @param remoteID:    Unique ID of the interface to which this
                                interface should be connected.
            @type  remoteID:    str
        """
        if not self._protocols:
            self.start()

        remoteID = UUID(bytes=remoteID)

        if protocol not in self._protocols:
            self._protocols[protocol] = set()

        assert remoteID not in self._protocols[protocol]
        self._protocols[protocol].add(remoteID)

        protocol.registerConnection(self, remoteID)

    def remote_disconnect(self, protocol, remoteID):
        """ Disconnect this interface from another interface.

            @param protocol:    Protocol instance which was used for the
                                connection.
            @type  protocol:    rce.slave.protocol._Protocol

            @param remoteID:    Unique ID of the interface from which this
                                interface should be disconnected.
            @type  remoteID:    str
        """
        remoteID = UUID(bytes=remoteID)

        protocol.unregisterConnection(self, remoteID)

        assert remoteID in self._protocols[protocol]
        self._protocols[protocol].remove(remoteID)

        if not self._protocols[protocol]:
            del self._protocols[protocol]

        if not self._protocols:
            self.stop()

    def remote_destroy(self):
        """ Method should be called to destroy the interface and will take care
            of deleting all circular references.
        """
        self.stop()

        if self._owner:
            self._owner.unregisterInterface(self)
            self._owner = None

        if self._owner._client._avatar:
            def eb(failure):
                if not failure.check(PBConnectionLost):
                    log.err(failure)

            try:
                self._owner._client._avatar.callRemote('interfaceDied').addErrback(eb)
            except (DeadReferenceError, PBConnectionLost):
                pass

    def start(self):
        """ This method is used to setup the interface.

            Don't overwrite this method; instead overwrite the hook _start.

            @raise:     rce.error.InternalError if the interface can not be
                        started.
        """
        if self._ready:
            return

        self._start()
        self._ready = True

    def stop(self):
        """ This method is used to stop the interface.

            Don't overwrite this method; instead overwrite the hook _stop.
        """
        if not self._ready:
            return

        self._stop()
        self._ready = False

    def send(self, msg, msgID, protocol, remoteID):
        """ This method is used to send a message to the endpoint.

            Don't overwrite this method; instead overwrite the method _send.
            If the interface does not overwrite the method _send, it is assumed
            that the interface does not support this action and an
            InternalError is raised when send is called.

            @param msg:         Message which should be sent in serialized
                                form.
            @type  msg:         str

            @param msgID:       Message ID which is used to match response
                                message.
            @type  msgID:       str

            @param protocol:    Protocol instance through which the message
                                was sent.
            @type  protocol:    rce.slave.protocol._Protocol

            @param remoteID:    Unique ID of the Interface which sent the
                                message.
            @type  remoteID:    uuid.UUID
        """
        if not self._ready:
            raise InternalError('Interface is not ready to send a message.')

        try:
            if remoteID not in self._protocols[protocol]:
                raise KeyError()
        except KeyError:
            log.msg('Received message dropped, because interface does not '
                    'expected the message.')

        self._send(msg, msgID, protocol, remoteID)

    def received(self, msg, msgID):
        """ This method is used to send a received message from the endpoint
            to the appropriate protocols.

            @param msg:         Message which should be sent in serialized
                                form.
            @type  msg:         str

            @param msgID:       Message ID which is used to match response
                                message.
            @type  msgID:       str
        """
        for protocol in self._protocols:
            protocol.sendMessage(self, msg, msgID)

    def respond(self, msg, msgID, protocol, remoteID):
        """ This method is used to send a received message from the endpoint
            to the specified protocol/interface as a response.

            @param msg:         Message which should be sent in serialized
                                form.
            @type  msg:         str

            @param msgID:       Message ID which is used to match response
                                message.
            @type  msgID:       str

            @param protocol:    Protocol instance to which the response should
                                be sent.
            @type  protocol:    rce.slave.protocol._Protocol

            @param remoteID:    Unique ID of the Interface to which the
                                response be sent.
            @type  remoteID:    uuid.UUID
        """
        protocol.sendMessage(self, msg, msgID, remoteID)

    ###
    ### Hooks which can / have to be overwritten in Interface implementation
    ###

    def _start(self):
        pass

    def _stop(self):
        pass

    def _send(self, msg, msgID, protocol, remoteID):
        raise InternalError('Interface does not support sending of a message.')
