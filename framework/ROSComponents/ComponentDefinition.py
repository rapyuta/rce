#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       ComponentDefinition.py
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

""" Message Content Identifier of ROS Messages of RCE Protocol:
        
        n   Node (for removal)
        i   Interface (for removal)
        p   Parameter (for removal)
        
        N   Node

        I   IntParam
        S   StrParam
        F   FloatParam
        B   BoolParam
        X   FileParam
        
        V   ServiceInterface
        P   PublisherInterface
        C   SubscriberInterface
"""

RM_NODE = 'n'
RM_INTERFACE = 'i'
RM_PARAMETER = 'p'

NODE = 'N'

PARAM_INT = 'I'
PARAM_STR = 'S'
PARAM_FLOAT = 'F'
PARAM_BOOL = 'B'
PARAM_FILE = 'X'

INTERFACE_SRV = 'V'
INTERFACE_PUB = 'P'
INTERFACE_SUB = 'C'

