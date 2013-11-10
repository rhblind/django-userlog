# -*- coding: utf-8 -*-

from django.conf import settings
from django.utils.text import get_text_list
from django.utils.encoding import force_unicode
from django.utils.translation import ugettext as _
from django.contrib.contenttypes.models import ContentType

from userlog.models import post_writelog
from userlog.models import UserLogEntry, ADDITION, CHANGE, DELETION


def construct_change_message(request, form, formsets=None):
    """
    Constructs a change message from a changed form
    and optionally a list of formsets.
    """
    
    change_message = []
    labels = None
    use_labels = getattr(settings, "USERLOG_LABEL_NAMES", False)
    
    if form.changed_data:
        if use_labels is True:
            labels = [form.fields[field].label for field in form.changed_data]
        change_message.append(_("Changed %s." % get_text_list(labels or form.changed_data, _("and"))))
    
    if formsets:
        for formset in formsets:
            # New objects
            for obj in formset.new_objects:
                change_message.append(_('Added %(name)s "%(object)s".') % {
                    "name": force_unicode(obj._meta.verbose_name),
                    "object": force_unicode(obj)
                })

            # Changed objects
            for obj, changed_fields in formset.changed_objects:
                labels = None
                # TODO: figure out a reliable way of solving this
#                if use_labels is True:
#                    labels = [f.verbose_name for f in obj._meta.fields if f.name in changed_fields]
                change_message.append(_('Changed %(list)s for %(name)s "%(object)s".') % {
                    "list": get_text_list(labels or changed_fields, _("and")),
                    "name": force_unicode(obj._meta.verbose_name),
                    "object": force_unicode(obj)
                })

            # Deleted objects
            for obj in formset.deleted_objects:
                change_message.append(_('Deleted %(name) "%(object)".') % {
                    "name": force_unicode(obj._meta.verbose_name),
                    "object": force_unicode(obj)
                })

    change_message = " ".join(change_message)
    return change_message or _("No fields changed.")


class UserLogCreateMixin(object):
    """
    Mixin for logging user actions on a CreateView.
    """
    
    def form_valid(self, form):
        self.object = form.save()
        
        # Only write log for models which are
        # configured to be logged.
        if getattr(self.object, "log_useractions", False):
            message = construct_change_message(self.request, form)
            self.write_log(self.request, self.object, message)

        return super(UserLogUpdateMixin, self).form_valid(form)
    
    def write_log(self, request, obj, message):
        """
        Log that an object has been successfully changed.
        """
        UserLogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=ContentType.objects.get_for_model(obj).pk,
            object_id=obj.pk, object_repr=force_unicode(obj), action_flag=ADDITION,
            change_message=message
        )
        post_writelog.send(sender=UserLogEntry, instance=obj, using=obj._state.db)


class UserLogUpdateMixin(UserLogCreateMixin):
    """
    Mixin for logging user actions on an UpdateView.
    """
    
    def write_log(self, request, obj, message):
        """
        Log that an object has been successfully changed.
        """
        UserLogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=ContentType.objects.get_for_model(obj).pk,
            object_id=obj.pk, object_repr=force_unicode(obj), action_flag=CHANGE,
            change_message=message
        )
        post_writelog.send(sender=UserLogEntry, instance=obj, using=obj._state.db)

        
class UserLogDeleteMixin(object):
    """
    Mixin for logging user actions on a DeleteView.
    """
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        # Only write log for models which are
        # configured to be logged.
        if getattr(self.object, "log_useractions", False):
            self.write_log(self.request, self.object, "message")

        return super(UserLogDeleteMixin, self).delete(request, *args, **kwargs)
    
    def write_log(self, request, obj, message):
        """
        Log that an object has been successfully changed.
        Note that this is called before deletion.
        """
        UserLogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=ContentType.objects.get_for_model(obj).pk,
            object_id=obj.pk, object_repr=force_unicode(obj), action_flag=DELETION,
            change_message=message
        )
        post_writelog.send(sender=UserLogEntry, instance=obj, using=obj._state.db)


class FullHistoryMixin(object):
    """
    Add all userlog changes to context as "log_history".
    Nice if you would like to display all changes
    regardless of who made them.
    """
    
    def get_context_data(self, **kwargs):
        context = super(FullHistoryMixin, self).get_context_data(**kwargs)
        if hasattr(self.object, "log_history"):
            history = self.object.log_history()
            context["log_history"] = history
        return context
