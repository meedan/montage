"""
    Defines all Django views for the admin app
"""
import itertools
import datetime
from django.views.generic import TemplateView
from django.contrib.auth import get_user_model
from django.shortcuts import redirect, get_object_or_404
from django.conf import settings
from django.http import HttpResponse
from django.utils import timezone

from greenday_core.email_templates import NEW_USER_INVITED_NO_PROJECT
from greenday_core.models import PendingUser, User
from greenday_core.utils import send_email
from .forms import InviteNewUserForm
from greenday_core.user_deletion import delete_storyful_optouts
import deferred_manager


class UserListView(TemplateView):
    """
        Django view to handle the user list page
    """
    template_name = "user_list.html"

    def get_context_data(self, **kwargs):
        """
            Gets the list of users
        """
        users = {
            u.email: u for u in itertools.chain(
                get_user_model().objects.exclude(username="deleted"),
                PendingUser.objects.all())
        }

        return {
            'users': sorted(
                users.values(),
                key=lambda o: o.email),
            'form': InviteNewUserForm()
        }

    def post(self, request, *args, **kwargs):
        """
            Handles form submissions to create a new user
        """
        form = InviteNewUserForm(request.POST)

        if form.is_valid():
            pu = PendingUser.objects.create(
                email=form.cleaned_data['email'],
                is_whitelisted=True
            )

            send_email(
                "You've been invited to join Montage",
                NEW_USER_INVITED_NO_PROJECT.format(
                    home_link='http://montage.storyful.com'),
                pu.email
            )
            return redirect('user_management')

        context = self.get_context_data(**kwargs)
        context['form'] = form

        return self.render_to_response(context)


user_list = UserListView.as_view()


class DeleteUserView(TemplateView):
    """
        Django view to handle the user deletion page
    """
    template_name = "delete_user.html"
    object_type = get_user_model()

    def get_context_data(self, **kwargs):
        """
            Gets the user
        """
        user = get_object_or_404(self.object_type, pk=kwargs['id'])

        return {
            'deletion_user': user
        }

    def post(self, request, *args, **kwargs):
        """
            Deletes the user
        """
        context = self.get_context_data(**kwargs)
        user = context['deletion_user']

        user.delete()

        return redirect("user_management")

delete_user = DeleteUserView.as_view()

class DeletePendingUserView(DeleteUserView):
    """
        Handles deletion of a pending user
    """
    object_type = PendingUser


delete_pending_user = DeletePendingUserView.as_view()


class ChangeUserWhitelistView(TemplateView):
    """
        Handles adding or removing the whitelist flag from a user
    """
    template_name = "change_user_whitelist.html"
    object_type = get_user_model()

    def get_context_data(self, **kwargs):
        """
            Gets the user
        """
        user = get_object_or_404(self.object_type, pk=kwargs['id'])

        return {
            'whitelist_user': user
        }

    def post(self, request, *args, **kwargs):
        """
            Adds or removes the whitelist flag from a user
        """
        context = self.get_context_data(**kwargs)
        user = context['whitelist_user']

        user.is_whitelisted = not user.is_whitelisted
        user.save(update_fields=['is_whitelisted'])

        return redirect("user_management")


change_user_whitelist = ChangeUserWhitelistView.as_view()


def keep_alive(request):
    """
        Simple request handler that can be hit by a cron to keep an
        App Engine instance running
    """
    return HttpResponse("OK, OK. I'm awake.")
