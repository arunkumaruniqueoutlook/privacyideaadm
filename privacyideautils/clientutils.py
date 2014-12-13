#!/usr/bin/python
# -*- coding: utf-8 -*-
#  privacyIDEA is a fork of LinOTP
#  May 08, 2014 Cornelius Kölbel
#  License:  AGPLv3
#  contact:  http://www.privacyidea.org
#
#  Copyright (C) 2010 - 2014 LSE Leading Security Experts GmbH
#  License:  AGPLv3
#  contact:  http://www.linotp.org
#            http://www.lsexperts.de
#            linotp@lsexperts.de
'''
This module is used for the communication of
the python based management clients
privacyidea-adm
'''

import urllib2
import httplib
import urllib
import re
import random
import sys
import logging.handlers
import cookielib
import traceback
import pprint
import requests

from etokenng import (etng,
                       etngError)

import json
import gettext

_ = gettext.gettext

TIMEOUT = 5
etng = False


file_opts = ['rf_file=']
ldap_opts = ['rl_uri=', 'rl_basedn=', 'rl_binddn=',
             'rl_bindpw=', 'rl_timeout=', 'rl_loginattr=',
             'rl_searchfilter=', 'rl_userfilter=',
             'rl_attrmap=']
ldap_opts_map = {'rl_uri': 'LDAPURI',
                 'rl_basedn': 'LDAPBASE',
                 'rl_binddn': 'BINDDN',
                 'rl_bindpw': 'BINDPW',
                 'rl_timeout': 'TIMEOUT',
                 'rl_searchfilter': 'LDAPSEARCHFILTER',
                 'rl_userfilter': 'LDAPFILTER',
                 'rl_attrmap': 'USERINFO',
                 'rl_loginattr': 'LOGINNAMEATTRIBUTE'
                 }


def showresult(rv):
    try:
        pp = pprint.PrettyPrinter(indent=4)
        print pp.pformat(rv['result'])
    except:
        print rv


class PrivacyIDEAClientError(Exception):
    """
    This class is used to throw client exceptions.
    """
    def __init__(self, eid=10, description="PrivacyIDEAClientError"):
        self.id = eid
        self.description = description
        
    def __str__(self):
        # here we lookup the error id - to translate
        return repr("ERR" + str(self.id) + ": " + self.description)


class response_obj(object):
    def __init__(self, status_code, json_object, text):
        self.status = status_code
        self.data = json_object
        self.text = text


class privacyideaclient(object):
    """
    This class is created to hold a connection to the privacyIDEA server

    It creates an authorization token that is sent in the HTTP header on each
    request.
    """

    def __init__(self, username, password, baseuri="http://localhost:5000"):
        """
        :param baseuri: The base of the server like http://localhost:5000
        :type baseuri: basestring
        """
        self.auth_token = None
        self.baseuri = baseuri
        self.set_credentials(username, password)
        self.log = logging.getLogger('privacyideaclient')

    def _send_response(self, r):
        if r.status_code >= 300:
            raise PrivacyIDEAClientError(eid=r.status_code,
                                          description=r.text)
        try:
            json_response = r.json()
        except:
            json_response = None

        return response_obj(r.status_code, json_response, r.text)

    def set_credentials(self, username, password):
        """
        set an authtoken from the privacyidea server by providing username
        and password

        :param username: The username of the administrator or user
        :param password: The credential of the user
        :return: None
        """
        r = requests.post("%s/auth" % self.baseuri,
                          data={"username":"username",
                                "password": "password"})

        if r.status_code == requests.codes.ok:
            res = r.json()
            result = res.get("result")
            if result.get("status") is True:
                self.auth_token = result.get("value", {}).get("token")

    def get(self, uripath, param=None):
        r = requests.get("%s%s" % (self.baseuri, uripath),
                         headers={"Authorization": self.auth_token},
                         params=param)
        return self._send_response(r)


    def post(self, uripath, param=None):
        r = requests.post("%s%s" % (self.baseuri, uripath),
                          headers={"Authorization": self.auth_token},
                          data=param)
        return self._send_response(r)

    def delete(self, uripath):
        r = requests.delete("%s%s" % (self.baseuri, uripath),
                            headers={"Authorization": self.auth_token})
        return self._send_response(r)

    def userlist(self, param):
        return self.get('/user/', param)

# TODO: Migration
#    def auditsearch(self, param):
#        return self.connect('/audit/search', param)

    def inittoken(self, param):
        return self.post('/token/init', param)

    def listtoken(self, param):
        return self.get('/token/', param)

#    def getserialbyotp(self, param):
#        return self.connect('/admin/getSerialByOtp', param)

    def copytokenpin(self, param):
        return self.post('/token/copypin', param)

    def assigntoken(self, param):
        return self.post('/token/assign', param)

    def unassigntoken(self, param):
        return self.post('/token/unassign', param)

    def resetfailcounter(self, param):
        return self.post('/token/reset', param)

    def resynctoken(self, param):
        return self.post('/token/resync', param)

    def tokenrealm(self, serial, realms):
        return self.post('/token/realm/%s' % serial,
                         {'realms': realms})

    def set(self, param):
        """
        This function is used for many purposes like
            setmaxfail
            setsyncwindow
            setotplen
        This depends on the contents of the param dictionary.
        """
        return self.post('/token/set', param)

    def get_policy(self, param={}):
        return self.get('/policy/%s' % policy.get("name"), param)

    def setscpin(self, param):
        return self.post('/token/setpin', param)

    def disabletoken(self, param):
        param['enable'] = 'False'
        return self.post('/token/disable', param)

    def enabletoken(self, param):
        param['enable'] = 'True'
        return self.post('/token/enable', param)

    def deletetoken(self, serial):
        return self.delete('/token/%s'% serial)

    def getconfig(self, param):
        return self.get('/system/', param)

    def setconfig(self, param):
        return self.post('/system/setConfig', param)

    def getrealms(self):
        return self.get('/realm/')

    def securitymodule(self, param={}):
        return self.connect('/system/setupSecurityModule', param)

    def setrealm(self, realmname, param):
        return self.post('/realm/%s' % realmname, param)

    def deleterealm(self, realmname):
        return self.delete('/realm/%s' % realmname)

    def setdefaultrealm(self, realm):
        return self.post('/defaultrealm/%s' % realm)

    def deletedefaultrealm(self):
        return self.delete('/defaultrealm')

    def deleteconfig(self, key):
        return self.delete('/system/%s' % key)

    def setresolver(self, param):
        response = None
        if 'resolver' not in param:
            raise PrivacyIDEAClientError(1201, _("When setting a resolver, "
                                                  "you need to specify"
                                                  "'resolver'."))
        if 'type' not in param:
            raise PrivacyIDEAClientError(1202, _("When setting a resolver, "
                                                  "you need to specify "
                                                  "'type'."))
        if param["type"].lower() == "passwd":
            param["type"] = "passwdresolver"
            if 'filename' not in param:
                raise PrivacyIDEAClientError(1203, _("When setting a flat "
                                                     "file resolver, you need"
                                                     "to specify 'filename'."))

            response = self.post('/resolver/%s' % param.get("resolver"), param)

        elif param['type'].lower() == 'ldap':
            raise NotImplementedError("TODO: Doing the Voodoo to set all "
                                      "these config keys")
        elif param['type'].lower() == 'sql':
            raise NotImplementedError("TODO: Doing the Voodoo to set all "
                                      "these config keys")
        else:
            raise PrivacyIDEAClientError(1204, _("Unknown resolver type"))

        return response

    def deleteresolver(self, resolvername):
        return self.delete("/resolver/%s" % resolvername)

    def getresolver(self, resolver=None):
        """
        Return a list of all resolvers.
        If a resolvername is specified, only this resolver is returned.
        :param resolver: resolvername
        :return:
        """
        if resolver:
            return self.get("/resolver/%s" % resolver)
        else:
            return self.get("/resolver/")


def dumpresult(status, data, tabformat=None):
    '''
    This function is used to print the Tokenlist in a nice viewable
    ascii table.
    '''
    if tabformat is None:
        tabformat = {'tabsize': [4, 16, 14, 20, 20, 4, 4, 4, 4],
                     'tabstr': ["%4s", "%16s", "%14s", "%20s", "%20s", "%4s", "%4s", "%4s", "%4s", "%4s"],
                        'tabdelim': '|',
                        'tabvisible': [0, 1, 2, 3, 4, 5, 6, 7, 8],
                        'tabhead': ['Id', 'Desc', 'S/N', 'User', 'Resolver',
                       'MaxFail', 'Active', 'FailCount', 'Window'],
                        'tabentry': ['id',
                        'description',
                        'serial',
                        'username',
                        'resolver',
                        'maxfail',
                        'active',
                        'failcount',
                        'sync_window']}

    tabsize = tabformat['tabsize']
    tabstr = tabformat['tabstr']
    tabdelim = tabformat['tabdelim']
    tabvisible = tabformat['tabvisible']
    tabhead = tabformat['tabhead']
    tabentry = tabformat['tabentry']

    # if not result['status']:
    if not status:
        print "The return status is false"
    else:

        head = tabentry

        # Set the default, if no tabformat or a wrong tabformat is passed
        if not len(tabvisible):
            for i in range(0, len(head)):
                tabvisible.append(i)
        if len(tabhead) < len(head):
            print "tabhead " + str(len(tabhead)) + " head " + str(len(head))
            for i in range(0, len(head)):
                tabhead.append('head')
        if len(tabsize) < len(head):
            for i in range(0, len(head)):
                tabsize.append(10)
        if len(tabstr) < len(head):
            for i in range(0, len(head)):
                tabstr.append("%10s")

        # value = result['value']
        # data = value['data']

        i = 0
        for t in tabhead:
            print tabstr[i] % str(t)[:tabsize[i]], tabdelim,
            i = i + 1
        print

        for token in data:
            i = 0
            for t in tabentry:
                # print tabstr[i] % str(token.get(t)).endcode('utf-8') [:tabsize[i]], tabdelim,
                # text=str(token.get(t)).encode('utf-8')
                text = token.get(t)
                if not type(token.get(t)) == unicode:
                    text = str(token.get(t))
                print tabstr[i] % text[:tabsize[i]], tabdelim,
                i = i + 1
            print
