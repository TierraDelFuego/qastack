#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Allow auto completion work on Wing IDE
if 0:
    import db

#########################################################################
## This scaffolding model makes your app work on Google App Engine too
#########################################################################

if request.env.web2py_runtime_gae:            # if running on Google App Engine
    db = DAL('gae')                           # connect to Google BigTable
    session.connect(request, response, db=db) # and store sessions and tickets there
    ### or use the following lines to store sessions in Memcache
    # from gluon.contrib.memdb import MEMDB
    # from google.appengine.api.memcache import Client
    # session.connect(request, response, db=MEMDB(Client())
else:                                         # else use a normal relational database
    #db = DAL('sqlite://storage.sqlite')       # if not, use SQLite or other DB
    db = DAL('mysql://web2py:py2web@localhost:3306/qastack')
## if no need for session
# session.forget()

#########################################################################
## Here is sample code if you need for
## - email capabilities
## - authentication (registration, login, logout, ... )
## - authorization (role based authorization)
## - services (xml, csv, json, xmlrpc, jsonrpc, amf, rss)
## - crud actions
## comment/uncomment as needed

import sys, os
from gluon.tools import *

# Adds our "modules" folder to our search path
path = os.path.join(request.folder, 'modules')
if not path in sys.path:
    sys.path.append(path)

# Import Authentication/Authorization
from CustomAuthentication import CustomAuthentication
# Misc Methods QA-Stack-Specific
from QAStackHelper import QAStackHelper
auth_user = CustomAuthentication(globals(), db)
stackhelper = QAStackHelper(globals(), db, auth_user)
service = Service(globals()) # for json, xml, jsonrpc, xmlrpc, amfrpc

# crud.settings.auth=auth                      # enforces authorization on crud
# mail=Mail()                                  # mailer
# mail.settings.server='smtp.gmail.com:587'    # your SMTP server
# mail.settings.sender='you@gmail.com'         # your email
# mail.settings.login='username:password'      # your credentials or None
# auth.settings.mailer=mail                    # for user email verification
# auth.settings.registration_requires_verification = True
# auth.settings.registration_requires_approval = True
# auth.messages.verify_email = \
#  'Click on the link http://.../user/verify_email/%(key)s to verify your email'
## more options discussed in gluon/tools.py
#########################################################################


#########################################################################
## Define your tables below, for example
##
## >>> db.define_table('mytable',Field('myfield','string'))
##
## Fields can be 'string','text','password','integer','double','boolean'
##       'date','time','datetime','blob','upload', 'reference TABLENAME'
## There is an implicit 'id integer autoincrement' field
## Consult manual for more options, validators, etc.
##
## More API examples for controllers:
##
## >>> db.mytable.insert(myfield='value')
## >>> rows=db(db.mytable.myfield=='value').select(db.mytable.ALL)
## >>> for row in rows: print row.id, row.myfield
#########################################################################
## Authentication Schema (2 tables)
db.define_table('auth_roles',
    Field('role_name', 'string', length=128, required=True),
    Field('role_min_score', 'integer', required=True),
    Field('color_designation', 'text', length=6, required=False, default=''),
    migrate=False)

db.define_table('auth_users',
    Field('auth_alias', 'string', length=255, required=True), # Whatever login name the user authenticated with
    Field('auth_passwd', 'string', length=255, required=True),
    Field('auth_created_on', 'datetime', required=True, default=request.now),
    Field('auth_modified_on', 'datetime', required=True, default=request.now),
    Field('is_enabled', 'boolean', required=True, default=True),
    Field('auth_role_id', db.auth_roles), migrate=False)

# System Properties - Used by the system itself
db.define_table('system_properties',
    Field('property_name', 'string', length=128, required=True),
    Field('property_desc', 'text', required=True),
    Field('property_value', 'text', required=True), migrate=False)

# Member Properties (Skeleton) (Available member Properties)
db.define_table('member_properties_skel',
    Field('property_name', 'string', length=128, required=True),
    Field('property_desc', 'text', required=True),
    Field('member_editable', 'boolean', default=False),
    Field('sort_order', 'integer', default=0, required=True), migrate=False)

# Member Properties (For each member)
db.define_table('member_properties',
    Field('auth_user', db.auth_users),
    Field('property_id', db.member_properties_skel),
    Field('property_value', 'string', length=255, required=True), migrate=False)

# Avatars
db.define_table('member_avatars',
    Field('content_type', 'string', length=128, required=True),
    Field('auth_user_id', 'integer', required=True),
    Field('avatar_image', 'blob', required=True, default=None),
    Field('avatar_active', 'boolean', required=True, default=True), migrate=False)

# Questions
db.define_table('questions',
    Field('title', 'string', length=255, required=True),
    Field('description', 'text', required=True),
    Field('created_by', db.auth_users),
    Field('created_on', 'datetime', required=True),
    Field('modified_by', db.auth_users),
    Field('modified_on', 'datetime', required=True),
    Field('votes_up', 'integer', required=True, default=0),
    Field('votes_dn', 'integer', required=True, default=0),
    Field('is_answered', 'boolean', required=True, default=False),
    Field('is_closed', 'boolean', required=True, default=False),
    Field('is_featured', 'boolean', required=True, default=False),
    Field('is_visible', 'boolean', required=True, default=True),
    Field('views', 'integer', required=True, default=1), migrate=False)

# Answers
db.define_table('answers',
    Field('question_id', db.questions),
    Field('description', 'text', required=True),
    Field('votes_up', 'integer', required=True, default=0),
    Field('votes_dn', 'integer', required=True, default=0),
    Field('created_by', db.auth_users),
    Field('created_on', 'datetime', required=True),
    Field('modified_by', db.auth_users),
    Field('modified_on', 'datetime', required=True),
    Field('is_answer', 'boolean', required=True, default=False),
    Field('is_visible', 'boolean', required=True, default=True),
    Field('is_outstanding', 'boolean', required=True, default=False),
          migrate=False)

# Comments - Comments get up/dn points but do not count towards the user's profile
db.define_table('comments',
    Field('c_type', 'text', required=True), # 'Q' or 'A'
    Field('qa_id', 'integer', required=True), # ID of question or answer
    Field('description', 'text', required=True),
    Field('votes_up', 'integer', required=True, default=0),
    Field('votes_dn', 'integer', required=True, default=0),
    Field('created_by', db.auth_users),
    Field('created_on', 'datetime', required=True),
    Field('modified_by', db.auth_users),
    Field('modified_on', 'datetime', required=True),
    Field('is_visible', 'boolean', required=True, default=True), migrate=False)

# Score Log
db.define_table('score_log',
    Field('l_type', 'string', required=True), # 'Q', 'A', 'C'
    Field('subtype', 'string', required=True), # 'voteup', 'votedn', 'offensive', 'outstanding', 'featured', 'accepted'
    Field('qac_id', 'integer', required=True),
    Field('points', 'integer', required=True),
    Field('sender', db.auth_users),
    Field('created_on', 'datetime', required=True), migrate=False)

# Simple Tag System
db.define_table('tags',
    Field('tagname', 'string', required=True, length=255),
    Field('is_enabled', 'boolean', required=True, default=True),
    Field('tag_cnt', 'integer', required=True, default=1),
    migrate=False)

# Tag/Question relationship
db.define_table('question_tags',
    Field('question_id', db.questions),
    Field('tag_id', db.tags), migrate=False)

# Question Subscriptions - Everytime the user subscribes to a question,
# an entry is made here
db.define_table('question_subscriptions',
    Field('auth_user_id', db.auth_users),
    Field('question_id', db.questions),
    Field('is_active', 'boolean', default=True, required=True), migrate=False)

# When a question is updated, an email notification would be sent to all the
# Subscribed users, a record will be created here for the cron job to pick up
# and process
db.define_table('subscriptions_notification',
    Field('subscription_id', db.question_subscriptions),
    Field('created_on', 'datetime', required=True),
    Field('processed_on', 'datetime', required=False, default=None), migrate=False) # Important

# "Queue" messages sent to the administrators (All admins can view )
db.define_table('admin_messages',
    Field('auth_user', 'string', length=255, required=True),
    Field('subject', 'string', length=255, required=True),
    Field('message', 'text', required=True),
    Field('creation_date', 'datetime', required=True),
    Field('read_flag', 'boolean', default=False, required=True), migrate=False)
