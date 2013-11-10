# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import userlog

from django.conf import settings
from django.db import models
from django.dispatch import dispatcher, receiver
from django.contrib.sites.models import Site
from django.contrib.admin.models import LogEntry
from django.utils.encoding import smart_unicode
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType

ADDITION = 1
CHANGE = 2
DELETION = 3

logger = userlog.userlogger


class UserLogEntryManager(models.Manager):
    """
    Inherit the contrib.admin LogEntryManager
    """
    def log_action(self, user_id, content_type_id, object_id, object_repr, action_flag, change_message=""):
        e = self.model(None, None, user_id, content_type_id, smart_unicode(object_id),
                       object_repr[:200], action_flag, change_message, site_id=Site.objects.get_current().pk)
        e.save()


class UserLogMixin(object):
    """
    Provide user log actions to a model.
    """
    
    @property
    def log_useractions(self):
        """
        Must return True if user actions should be logged
        for this model.
        """
        return True
    
    def log_history(self):
        """
        Returns the entire user log history for given model
        instance, regardless of who made the change.
        """
        
        ctype, pk = ContentType.objects.get_for_model(self), self.pk
        queryset = UserLogEntry.objects.select_related("content_type", "user") \
            .filter(content_type=ctype, object_id=smart_unicode(pk), site__pk=settings.SITE_ID)
        return queryset


class UserLogEntry(LogEntry):
    """
    Inherits the contrib.admin LogEntry model.
    """
    
    objects = UserLogEntryManager()

    site = models.ForeignKey(Site, default=Site.objects.get_current)
    
    class Meta:
        verbose_name = _("user log entry")
        verbose_name_plural = _("user log entries")
        db_table = "userlog_entry"
        ordering = ("-action_time",)
    
    def __unicode__(self):
        if self.action_flag == ADDITION:
            return _('Added "%(object)s".') % {"object": self.object_repr}
        elif self.action_flag == CHANGE:
            return _('Changed "%(object)s" - %(changes)s') % {"object": self.object_repr, "changes": self.change_message}
        elif self.action_flag == DELETION:
            return _('Deleted "%(object)s."') % {"object": self.object_repr}

        return _("UserLogEntry Object")


#
# Signals
#

post_writelog = dispatcher.Signal(providing_args=["instance", "using"])


@receiver(post_writelog)
def post_writelog_handler(sender, instance, **kwargs):
    """
    Log that a debug message to the logging system.
    """
    logger.debug("userlog written for %r" % instance)
