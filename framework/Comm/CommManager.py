#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       CommManager.py
#       
#       This file is part of the RoboEarth Cloud Engine framework.
#       
#       This file was originally created for RoboEearth - http://www.roboearth.org/
#       The research leading to these results has received funding from the European Union 
#       Seventh Framework Programme FP7/2007-2013 under grant agreement no248942 RoboEarth.
#       
#       Copyright 2012 RoboEarth
#       
#       Licensed under the Apache License, Version 2.0 (the "License");
#       you may not use this file except in compliance with the License.
#       You may obtain a copy of the License at
#       
#       http://www.apache.org/licenses/LICENSE-2.0
#       
#       Unless required by applicable law or agreed to in writing, software
#       distributed under the License is distributed on an "AS IS" BASIS,
#       WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#       See the License for the specific language governing permissions and
#       limitations under the License.
#       
#       \author/s: Dominique Hunziker <dominique.hunziker@gmail.com> 
#       
#       

# zope specific imports
from zope.interface.verify import verifyObject
from zope.interface.exceptions import Invalid

# twisted specific imports
from twisted.python import log

# Python specific imports
from threading import Lock

# Custom imports
from Exceptions import InternalError
from Message.Interfaces import IContentSerializer, IMessageProcessor
from Message import MsgDef
from Message.Handler import send
from Message.StdType import InitMessage, RouteMessage
from Message.StdProcessor import RouteProcessor
from Router import Router

class CommManager(object):
    """ Class which is responsible for handling the communication.
    """
    def __init__(self, reactor, commID):
        """ Initialize the CommManager.

            @param reactor:     Reference to used reactor (from twisted).
            @type  reactor:     reactor

            @param commID:  CommID of this node which can be used by other
                            nodes to identify this node.
            @type  commID:  str
        """
        # Communication ID of this node
        self._commID = commID
        
        # twisted reactor which is used in this manager
        self._reactor = reactor
        
        # Reference to Router
        self._router = Router()
        
        # Message number counter
        self._msgNr = 0
        
        # Lock to be sure of thread-safety
        self._msgNrLock = Lock()
        
        # Content serializers
        self._contentSerializer = {}
        self.registerContentSerializers([ InitMessage(),
                                          RouteMessage() ])
        
        # Message processors
        self._processors = {}
        self.registerMessageProcessors([ RouteProcessor(self) ])
    
    @property
    def commID(self):
        """ Communication ID of this node. """
        return self._commID
    
    @property
    def reactor(self):
        """ Reactor instance of this node. """
        return self._reactor
    
    @property
    def router(self):
        """ Router instance of this node. """
        return self._router
    
    def registerContentSerializers(self, serializers):
        """ Method to register a content serializer which are used for serializing/deserializing
            the messages. If there already exists a serializer for the same message type the
            old serializer is dropped.
            
            @param serializers:     Content serializers which should be registered.
            @type  serializers:     [ IContentSerializer ]
            
            @raise:     InternalError if the serializers do not implement the "IContentSerializer"
                        interface.
        """
        for serializer in serializers:
            try:
                verifyObject(IContentSerializer, serializer)
            except Invalid as e:
                raise InternalError(
                    'Verification of the class "{0}" for the Interface "IContentSerializer" failed: {1}'.format(
                        serializer.__class__.__name__,
                        e 
                    )
                )
            
            self._contentSerializer[serializer.IDENTIFIER] = serializer
    
    def registerMessageProcessors(self, processors):
        """ Method to register a message processor which are used for the incoming messages.
            If there already exists a message processor for the same message type the old
            message processor is dropped.
                                
            @param processors:  Processor which should be registered.
            @type  processors:  [ IMessageProcessor ]
            
            @raise:     InternalError if the processors do not implement the "IMessageProcessor"
                        interface.
        """
        for processor in processors:
            try:
                verifyObject(IMessageProcessor, processor)
            except Invalid as e:
                raise InternalError(
                    'Verification of the class "{0}" for the Interface "IMessageProcessor" failed: {1}'.format(
                        processor.__class__.__name__,
                        e
                    )
                )
            
            self._processors[processor.IDENTIFIER] = processor
    
    def getMessageNr(self):
        """ Returns a new message number.
        """
        with self._msgNrLock:
            nr = self._msgNr
            self._msgNr = (self._msgNr + 1) % MsgDef.MAX_INT
        
        return nr
    
    def getSerializer(self, msgType):
        """ Returns the ContentSerializer matching the given msgType or None if there
            was no match.
        """
        return self._contentSerializer.get(msgType, None)
    
    def sendMessage(self, msg):
        """ Send a message.

            @param msg:     Message which should be sent.
            @type  msg:     Message
        """
        send(self, msg)
    
    def processMessage(self, msg):
        """ Process the message using the registered message processors.
            
            @param msg:     Received message.
            @type  msg:     Message
        """
        if msg.msgType in self._processors:
            self._processors[msg.msgType].processMessage(msg)
        else:
            log.msg('Received a message whose type ("{0}") can not be handled by this CommManager.'.format(msg.msgType))
    
    def shutdown(self):
        """ Method which should be used when the CommManager is terminated.
            It is used to remove circular references.
        """
        self._contentSerializer = {}
        self._processors = {}
