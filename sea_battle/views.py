

import json

from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils.timezone import now
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import FormView, TemplateView
from datetime import timedelta, datetime
from sea_battle.models import BattleMap, Game

from sea_battle.utils import sorted_fleet, prepare_to_store


class HelloView(TemplateView):

    template_name = 'index.html'

    def get(self, request, *args, **kwargs):

        template = HelloView.template_name

        return render(
            request,
            template)


class RegisterFormView(FormView):

    form_class = UserCreationForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('see_users')

    def form_valid(self, form):
        form.save()
        user = authenticate(  # for redirecting after registration to success_url with ontime authentificate
            request=self.request,
            username=form.cleaned_data['username'],
            password=form.cleaned_data['password1']
        )
        login(self.request, user)
        return super(RegisterFormView, self).form_valid(form)


class SeeUsersView(FormView):

    template_name = 'playerlist.html'

    # your opponents in game.
    # You point the user that you want to create a game with
    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        starting_time = now() - timedelta(seconds=60)

        online_users = User.objects.filter(onlineuseractivity__last_activity__gte=starting_time)

        games = Game.objects.filter(creator__in=online_users, joiner=None).exclude(creator=request.user)

        cleared_users = games.values_list('creator__username', 'id', 'size', 'game_name')

        cleared_users = json.dumps(list(cleared_users))

        return render(
            request,
            SeeUsersView.template_name,
            context={
                "online_users": cleared_users,
            }
        )


class GameNewView(FormView):

    template_name = 'pre_battle.html'

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):

        size = int(request.POST.get('fld_size'))
        game_name = request.POST.get('Name_of_game')
        sizeiterator = list(range(size))
        opponent = request.POST.get('opponent_username')

        return render(
            request,
            GameNewView.template_name,
            context={
                'size': size,
                'sizeiterator': sizeiterator,
                'opponent': opponent,
                'game_name': game_name,
            }
        )


class GameJoinView(FormView):

    template_name = 'pre_battle.html'

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):

        opponent = request.POST.get('opponent_username')
        username_id = User.objects.get(username=opponent).id

        # retrieving size of created game

        # size = BattleMap.objects.get(user=username_id).map_of_bf['size']

        # set joined username as opponent at user, who has created game

        # tmp = BattleMap.objects.get(user=username_id).map_of_bf
        # tmp['opponent_username'] = request.user.username
        # BattleMap.objects.filter(user=username_id).update(map_of_bf=tmp)
        sizeiterator = list(range(int(size)))

        return render(
            request,
            GameJoinView.template_name,
            context={
                'size': size,
                'sizeiterator': sizeiterator,
                'opponent': opponent,
            }
        )


class GamePlayViewForCreator(FormView):

    template_name = 'battle.html'

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):

        if request.method == 'POST':

            data = json.loads(request.POST.get('json_form'))

            sorted_fleet_list = sorted_fleet(data['fleet'])
            size = data['size']
            opponent = data['opponent_username']
            if data['game_name'] == 'Name of your game':
                game_name = "Noname"
            else:
                game_name = data['game_name']

            game = Game.objects.create(
                size=size,
                turn=request.user,
                date=datetime.now(),
                creator=request.user,
                joiner=None,
                game_name=game_name,
            )
            a = prepare_to_store(sorted_fleet_list)
            BattleMap.objects.create(
                user=request.user,
                fleet_new=a,
                shoots=[],
                game=game,
            )

            username_id = User.objects.get(username=request.user).pk
            battlemap = BattleMap.objects.get(user=username_id, game=game)
            respjson = battlemap.fleet_new
            game_id = battlemap.game.pk
            get_size = Game.objects.get(creator=username_id, pk=game_id).size
            sizeiter = list(range(get_size))
            data = json.dumps(respjson)
            try:
                # for joiner this block has success, as joiner has particular opponent
                # here we try to get enemy's map
                username_id = User.objects.get(username=opponent).pk
                joined_resp = BattleMap.objects.get(user=username_id).fleet_new
                joined_resp = json.dumps(joined_resp)
            except:
                joined_resp = {}
            return render(
                request,
                GamePlayViewForCreator.template_name,

                context={
                    'form':         data,
                    'sizeiterator': sizeiter,
                    'size':         get_size,
                    'opponent':     opponent,
                    'joined_map':   joined_resp
                }
            )


class GamePlayViewForJoiner(FormView):

    template_name = 'battle.html'

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):

        if request.method == 'POST':

            data = json.loads(request.POST.get('json_form'))

            sorted_fleet_list = sorted_fleet(data['fleet'])
            size = data['size']
            opponent = data['opponent_username']
            if data['game_name'] == 'Name of your game':
                game_name = None
            else:
                game_name = data['game_name']

            print("sorted_fleet:", sorted_fleet_list)

            opponent_id = User.objects.get(username=opponent).pk
            game = Game.objects.get(creator=opponent_id, game_name=game_name)

            battlemap = BattleMap.objects.get(user=opponent_id, game=game)
            respjson = battlemap.fleet
            game_id = battlemap.game.pk



