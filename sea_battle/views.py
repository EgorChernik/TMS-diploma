import json
from django.contrib.auth.forms import UserCreationForm
from django.core import serializers
from django.http import HttpResponse, HttpRequest, HttpResponseRedirect
from django.shortcuts import render, render_to_response
from django.contrib.auth.decorators import login_required
from django.views import View
from django.views.generic import FormView, TemplateView
import online_users.models
from datetime import timedelta

from sea_battle.forms import GameAttrForm
from .models import BattleMap

class HelloView(TemplateView):

    template_name = 'index.html'
    def get(self,request, *args, **kwargs):
        template = HelloView.template_name
        return render(
            request,
            template)

class RegisterFormView(FormView):

    form_class = UserCreationForm
    success_url = '../login/' #не знаю, как реализовать более изящно. reverse and redirect не помогли
    template_name = "registration/signup.html"

    def form_valid(self, form):
        form.save()
        return super(RegisterFormView, self).form_valid(form)

class SeeUsersView(FormView):

    template_name = 'playerlist.html'

    #your opponents in game. You point the user that you want to create a game with
    #https://stackoverflow.com/questions/29663777/how-to-check-whether-a-user-is-online-in-django-template

    def get(self, request, *args, **kwargs):
        user_status = online_users.models.OnlineUserActivity.get_user_activities(timedelta(seconds=60))
        users = (user for user in user_status)
        return render(
            request,
            SeeUsersView.template_name,
            context={
                 "users": users,
            }
        )

class GameNewView(FormView):

    template_name = 'pre_battle.html'

    def post(self, request, *args, **kwargs):

        size = int(request.POST.get('fld_size'))
        print(size)
        sizeiterator = list(range(size))
        opponent = request.POST.get('opponent_username')
        a = dict(request.POST)
        print('a1: ', a)
        return render(
            request,
            GameNewView.template_name,
            context={
            'size': size,
            'sizeiterator': sizeiterator,
            'opponent': opponent,
            }
        )

    # памятник моим мучениям
    # def gameplay1(request, *args, **kwargs):
    #     a= dict(request.POST)
    #     print('a: ', a)  # если аяксом отпр
    #     if BattleMap.objects.values_list("map1_of_btlfld", flat=True):
    #         BattleMap.objects.update(map1_of_btlfld=request.POST.get('json_place'))
    #     else:
    #         BattleMap.objects.create(map1_of_btlfld=request.POST.get('json_place')).save()
    #
    #     def json_view(request):
    #         qs = BattleMap.objects.all()
    #         qs_json = serializers.serialize('json', qs)
    #         print('qs_json: ', qs_json)
    #         return qs_json
    #     map1 = json.loads(json_view(request))
    #     print(12345)
    #     dict_map1 = json.loads(map1[0]['fields']['map1_of_btlfld'])
    #     print(type(dict_map1['size']))
    #     return render(
    #         request,
    #         'sea_battle/battle.html',
    #         {'dict_map1': dict_map1}
    #     )

class GamePlayView(FormView):

    template_name = 'battle.html'

    def get(self, request,*args,**kwargs):
        if request.method == 'POST': # If the form has been submitted...
            form = GameAttrForm(request.POST) # A form bound to the POST data
            if form.is_valid(): # All validation rules pass
                # Process the data in form.cleaned_data
                # ...
                print('form is ok')
                print(form.cleaned_data['map1_of_btlfld'])
            else:
                print('form is invalid')
            return HttpResponseRedirect('/game/') # Redirect after POST
        else:
            form = GameAttrForm() # An unbound form
        print(form.fields)
        return render(
            request,
            GameNewView.template_name,
            context={
            'form': form,
        })