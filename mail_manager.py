#!/usr/bin/env python
import sys
import time
import smtplib
import MySQLdb

SYSTEM_NAME = "QA-Stack Website"
SITE_ROOT = 'http://www.qa-stack.com/qa-stack'
SMTP_SERVER = '208.70.149.41'

def send_mail(message, recipient, subject, dry_run_flag):
    """ Send a regular email """

    #now = time.strftime('%m/%d/%Y %I:%M %p')
    now = time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime())
    sender = '"QA-Stack System" <noreply@pyforum.org>'

    session    = smtplib.SMTP(SMTP_SERVER)

    mto = 'To: "QA-Stack.com Member" <%s>\n' % (recipient)
    mfrom = 'From: %s\n'    % (sender)
    msubj = 'Subject: %s\n' % (subject)
    mdate = 'Date: %s\n\n'  % (now)
    mbody = '%s\n'          % (message)

    email = '%s%s%s%s%s'  % (mto, mfrom, msubj, mdate, mbody)
    if dry_run_flag:
        print "%s\n%s\n%s" % (('*' * 50), email, ('*' * 50))
        return 0
    else:
        try:
            rval = session.sendmail(sender,recipient,email)
            return len(rval.keys())
        except:
            return -1

flag = ''
if len(sys.argv) <= 2:
    try:
        flag = sys.argv[1]
    except IndexError:
        flag = ''
flag = flag.lower()

if flag and flag not in ['--dry-run', '--help']:
    print "Usage: %s [--dry-run|--help]" % (sys.argv[0])
    sys.exit(1)

if flag == '--help':
    print "Run this program without any parameters to send the emails out to the subscribers."
    print "If you run this program with the --dry-run flag, the system will process everything normally"
    print "but no emails will be sent and no database update will take place."
    sys.exit(2)

sql_get_topics = """
    select
        sn.id,
        sn.subscription_id,
        sn.creation_date,
        sn.auth_user,
        u.auth_email,
        t.title as topic_title
    from
        zf_member_subscriptions_notification as sn,
        auth_users as u,
        zf_topic as t
    where
        u.auth_alias = sn.auth_user
        and sn.subscription_type = 'T'
        and t.id = sn.subscription_id
        and sn.is_processed = 'F'
    group by
        sn.subscription_id,
        u.auth_email
"""

sql_get_forums = """
    select
        sn.id,
        sn.subscription_id,
        sn.creation_date,
        sn.auth_user,
        u.auth_email,
        f.forum_title
    from
        zf_member_subscriptions_notification as sn,
        auth_users as u,
        zf_forum as f
    where
        u.auth_alias = sn.auth_user
        and sn.subscription_type = 'F'
        and f.id = sn.subscription_id
        and sn.is_processed = 'F'
    group by
        sn.subscription_id,
        u.auth_email
"""

topic_email = """Dear %s,

A topic for which you have requested email notifications has been updated. You are receiving this email because you have subscribed to this topic.

The topic is: %s

Please visit the topic thread located at %s/default/view_topic/%s

If you wish to unsubscribe from this topic, please log in to %s and click on the "My Preferences" link.

pyForum Administrator.
"""

forum_email = """Dear %s,

A forum for which you have requested email notificatons has been updated. You are receiving this email because you have subscribed to this forum.

The Forum is: %s

Please visit the Forum located at %s/default/view_forum/%s

If you wish to unsubscribe from this forum, please log in to %s and click on the "My Preferences" link.

pyForum Administrator.
"""

dbconn = MySQLdb.connect(host='localhost',db='zforum',user='jschwarzbeck',passwd='dderidex')
# Set-up a cursor
cursor = dbconn.cursor()

# Forums
cursor.execute(sql_get_forums)
forum_subscriptions = cursor.fetchall()
if forum_subscriptions:
    subject = 'A Forum has been updated in %s' % (SYSTEM_NAME)
    for subscription in forum_subscriptions:
        forum_id = subscription[1]
        user = subscription[3]
        email = subscription[4]
        forum_title = subscription[5]
        email_msg = forum_email % (user, forum_title, SITE_ROOT, forum_id, SITE_ROOT)
        sendmail_flag = send_mail(message=email_msg, recipient=email, subject=subject, dry_run_flag=flag)
        if flag != '--dry-run':
            if sendmail_flag == 0:
                sql = "update zf_member_subscriptions_notification set is_processed = 'T' where subscription_id = %s and auth_user = '%s'" % (forum_id, user)
                cursor.execute(sql)
            elif sendmail_flag == -1:
                print "Unable to send the email to %s <%s>, it is possible that the mail server refused your connection parameters." % (user, email)
            else:
                print "There was a problem sending email to %s <%s>, please check your log files for more information." % (user, email)
else:
    print "No Forum Subscriptions Found."

# Topics
cursor.execute(sql_get_topics)
topic_subscriptions = cursor.fetchall()
if topic_subscriptions:
    subject = 'A Topic has been updated in %s' % (SYSTEM_NAME)
    for subscription in topic_subscriptions:
        topic_id = subscription[1]
        user = subscription[3]
        email = subscription[4]
        topic_title = subscription[5]
        email_msg = topic_email % (user, topic_title, SITE_ROOT, topic_id, SITE_ROOT)
        sendmail_flag = send_mail(message=email_msg, recipient=email, subject=subject, dry_run_flag=flag)
        if flag != '--dry-run':
            if sendmail_flag == 0:
                sql = "update zf_member_subscriptions_notification set is_processed = 'T' where subscription_id = %s and auth_user = '%s'" % (topic_id, user)
                cursor.execute(sql)
            elif sendmail_flag == -1:
                print "Unable to send the email to %s <%s>, it is possible that the mail server refused your connection parameters." % (user, email)
            else:
                print "There was a problem sending email to %s <%s>, please check your log files for more information." % (user, email)
else:
    print "No Topic Subscriptions Found."

cursor.close()
dbconn.commit()
dbconn.close()

