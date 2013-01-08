# -*- coding: utf-8 -*-

from userlog.models import post_writelog
from django.utils.encoding import force_unicode
from django.contrib.contenttypes.models import ContentType
from userlog.models import UserLogEntry, ADDITION, CHANGE, DELETION


class UserLogCreateMixin(object):
    """
    Mixin for logging user actions on a CreateView.
    """
    
    def form_valid(self, form):
        self.object = form.save()
        
        # Only write log for models which are
        # configured to be logged.
        if getattr(self.object, "log_useractions", False):
            self.write_log(self.request, self.object, "message")
        return super(UserLogUpdateMixin, self).form_valid(form)
    
    def write_log(self, request, obj, message):
        """
        Log that an object has been successfully changed.
        """
        UserLogEntry.objects.log_action(user_id=request.user.pk,
            content_type_id=ContentType.objects.get_for_model(obj).pk,
            object_id=obj.pk, object_repr=force_unicode(obj), action_flag=ADDITION,
            change_message=message)
        post_writelog.send(sender=UserLogEntry, instance=obj, using=obj._state.db)


class UserLogUpdateMixin(UserLogCreateMixin):
    """
    Mixin for logging user actions on an UpdateView.
    """
    
    def write_log(self, request, obj, message):
        """
        Log that an object has been successfully changed.
        """
        UserLogEntry.objects.log_action(user_id=request.user.pk,
            content_type_id=ContentType.objects.get_for_model(obj).pk,
            object_id=obj.pk, object_repr=force_unicode(obj), action_flag=CHANGE,
            change_message=message)

        
class UserLogDeleteMixin(object):
    """
    Mixin for logging user actions on a DeleteView.
    """
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if getattr(self.object, "log_useractions", False):
            self.write_log(self.request, self.object, "message")
        return super(UserLogDeleteMixin, self).delete(request, *args, **kwargs)
    
    def write_log(self, request, obj, message):
        """
        Log that an object has been successfully changed.
        Note that this is called before deletion.
        """
        UserLogEntry.objects.log_action(user_id=request.user.pk,
            content_type_id=ContentType.objects.get_for_model(obj).pk,
            object_id=obj.pk, object_repr=force_unicode(obj), action_flag=DELETION,
            change_message=message)


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
