# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from __future__ import absolute_import

from django.conf import settings
from django import template
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import smart_unicode

from userlog.models import UserLogEntry
from django.contrib.auth.models import User

register = template.Library()


class BaseUserLogNode(template.Node):
    """
    Base helper class for handling userlog tags.
    """
    
    @classmethod
    def handle_token(cls, parser, token):
        """
        Class method to parse userlog tokens and return a Node.
        """
        
        tokens = token.contents.split()
        if len(tokens) < 8:
            raise template.TemplateSyntaxError("%r tag requires 7 or 8 arguments." % tokens[0])
        if not tokens[1].isdigit():
            raise template.TemplateSyntaxError("First argument to '%r' must be an integer." % tokens[0])
        if tokens[2] != "for":
            raise template.TemplateSyntaxError("Second argument to '%r' must be 'for'." % tokens[0])
        
        # {% get_user_log 10 for obj as varname for_user 42 %}
        if len(tokens) == 8:
            if tokens[4] != "as":
                raise template.TemplateSyntaxError("Fourth argument to '%r' must be 'as'." % tokens[0])
            return cls(limit=tokens[1], object_expr=parser.compile_filter(tokens[3]), as_varname=tokens[5],
                       for_user=parser.compile_filter(tokens[7]))

        # {% get_user_log 10 for app_label.model 54 as varname for_user 42 %}
        elif len(tokens) == 9:
            if tokens[5] != "as":
                raise template.TemplateSyntaxError("Fifth argument to '%r' must be 'as'." % tokens[0])
            return cls(limit=tokens[1], ctype=BaseUserLogNode.lookup_content_type(tokens[3], tokens[0]),
                       object_id_expr=parser.compile_filter(tokens[4]), as_varname=tokens[6],
                       for_user=parser.compile_filter(tokens[8]))
        else:
            raise template.TemplateSyntaxError("%r tag requires exactly 7 or 8 arguments." % tokens[0])

    @staticmethod
    def lookup_content_type(token, tagname):
        try:
            app, model = token.split(".")
            return ContentType.objects.get_by_natural_key(app, model)
        except ValueError:
            raise template.TemplateSyntaxError("Third argument in '%r' must be in the "
                                               "format 'app.model'" % tagname)
        except ContentType.DoesNotExist:
            raise template.TemplateSyntaxError("'%r' tag has non-existant content-type: '%s:%s'" %
                                               (tagname, app, model))

    def __init__(self, limit=None, ctype=None, object_id_expr=None, object_expr=None, as_varname=None, for_user=None):
        
        if ctype is None and object_expr is None:
            raise template.TemplateSyntaxError("UserLog nodes must be given either a literal object "
                                               "or a ctype and object pk.")
        self.model = UserLogEntry
        self.limit = limit
        self.ctype = ctype
        self.object_id_expr = object_id_expr
        self.object_expr = object_expr
        self.as_varname = as_varname
        self.for_user_expr = for_user
            
    def render(self, context):
        qset = self.get_queryset(context)
        context[self.as_varname] = self.get_context_value_from_queryset(context, qset)
        return ""
    
    def get_queryset(self, context):
        ctype, object_id = self.get_target_ctype_pk(context)
        for_user = self.get_for_user_pk(context)
        if not object_id:
            return self.model.objects.none()
        
        q = Q(content_type=ctype, object_id=smart_unicode(object_id), site__pk=settings.SITE_ID)
        if for_user is not None:
            q = q & Q(user=for_user)

        qset = self.model.objects.select_related("content_type", "user").filter(q)
        return qset
    
    def get_target_ctype_pk(self, context):
        """
        Resolve and returns the target object.
        """
        if self.object_expr:
            try:
                obj = self.object_expr.resolve(context)
            except template.VariableDoesNotExist:
                return None, None
            return ContentType.objects.get_for_model(obj), obj.pk
        else:
            return self.ctype, self.object_id_expr.resolve(context, ignore_failures=True)
        
    def get_for_user_pk(self, context):
        """
        Resolve and returns a User instance.
        """
        if self.for_user_expr:
            try:
                obj = self.for_user_expr.resolve(context)
                if not isinstance(obj, (User, int)):
                    raise template.TemplateSyntaxError("'for_user' argument must be given either "
                                                       "a literal user object instance or a user pk.")
                elif isinstance(obj, int):
                    obj = User.objects.get(pk=obj)
            except template.VariableDoesNotExist, User.DoesNotExist:
                return None
            return obj
        else:
            user = context["user"]
            if user.is_authenticated():
                return user
            else:
                return None
    
    def get_context_value_from_queryset(self, context, qset):
        """
        Subclasses should override this.
        """
        raise NotImplementedError
        
        
class UserLogNode(BaseUserLogNode):
    """
    Something clever
    """
    
    def __repr__(self):
        return "<UserLog Node>"
    
    def get_context_value_from_queryset(self, context, qset):
        return list(qset[:self.limit])


@register.tag
def get_user_log(parser, token):
    """
    Populates a template variable with the user log for the given criteria.

    Usage::

        {% get_user_log [limit] for [object] as [varname] for_user [user] %}
        {% get_user_log [limit] for [app].[model] [object_id] as [varname] for_user [user] %}

    Examples::

        {% get_user_log 10 for event as user_log for_user 23 %}
        {% get_user_log 10 for calendar.event 86 as calendar_log for_user user %}
        {% get_user_log 10 for calendar.event event.id as calendar_log for_user 54 %}

    Note that ``user`` can be a hard-coded integer
    (user ID) or the name of a template context variable containing the user
    object whose ID you want.
    """
    return UserLogNode.handle_token(parser, token)
