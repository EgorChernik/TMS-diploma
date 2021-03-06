
from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone

from rest_framework import viewsets, generics, exceptions
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from rest_framework import status

from sea_battle import constants
from sea_battle.api import serializers, validators
from sea_battle.models import BattleMap, Game
from sea_battle.services import get_game, get_game_state, handle_shoot, \
    create_game, join_game, join_fleet, create_user, get_game_battle_maps
from sea_battle.utils import mapped_shoots


class CleaningAPIView(generics.GenericAPIView):

    # deleting map of player, when the window is being hidden by him

    def get(self, request, *args, **kwargs):
        BattleMap.objects.filter(user=request.user).delete()
        resp = {"window.onclose event": "Deleting map successfully completed"}
        self.get_queryset()
        return JsonResponse(resp)


class RegisterFormAPIViewSet(viewsets.GenericViewSet):

    permission_classes = (AllowAny,)

    def get_queryset(self):

        return self.request.data

    def create(self, request, *args, **kwargs):
        # Validation

        validator = validators.SignUpValidator(data=request.data)
        validator.is_valid(raise_exception=True)

        user = create_user(validator.validated_data)

        token, created = Token.objects.get_or_create(user=user)
        resp = {'token': token.key, 'username': user.username}
        return Response(resp, status=status.HTTP_201_CREATED)


class WatchGamesAPIViewSet(viewsets.GenericViewSet):

    serializer_class = serializers.ActiveGamesSerializer
    permission_classes = (IsAuthenticated,)
    authentication_classes = (TokenAuthentication,)

    def get_queryset(self):
        current_user = self.request.user
        games = Game.objects.active_games().exclude(
            Q(creator=current_user) | Q(joiner=current_user)
        )
        return games

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        return Response(serializer.data)


class InitialDataAPIViewSet(viewsets.GenericViewSet):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def list(self, request, *args, **kwargs):

        current_user = request.user
        initial_data = {
            'fleet_composition': constants.FLEET_COMPOSITION,
            'username': current_user.username,
            'isAuthenticated': current_user.is_authenticated
        }

        return Response(initial_data)


class GamesAPIViewSet(viewsets.GenericViewSet):

    serializer_class = serializers.NewGameSerializer
    lookup_url_kwarg = 'game_id'
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        current_user = self.request.user

        return Game.objects.filter(
            Q(creator=current_user) | Q(joiner=current_user)
        )

    def list(self, request, *args, **kwargs):

        games = Game.objects.available_games().exclude(creator=request.user)
        self.serializer_class = serializers.AvailableGamesSerializer
        serializer = self.get_serializer(games, many=True)

        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        # Validation
        validator = validators.NewGameValidator(data=request.data)
        validator.is_valid(raise_exception=True)

        fleet_composition_errors = validator.check_fleet_composition()
        if fleet_composition_errors:

            return Response(
                fleet_composition_errors,
                status=status.HTTP_400_BAD_REQUEST)

        # Pass validated data to business logic (service)
        game, battlemap = create_game(validator.validated_data, request.user)

        # Serialization
        data = serializers.NewGameSerializer(game).data

        return Response(data, status=status.HTTP_201_CREATED)

    @action(methods=['PATCH'], detail=True)
    def shoot(self, request, game_id, **kwargs):

        game = get_game(game_id, request.user)
        if game.turn == request.user:

            validator = validators.ShootValidator(data=request.data)
            validator.is_valid(raise_exception=True)
            shoot = validator.validated_data['shoot']

            shoot_result, dead_zone, dead_ship = handle_shoot(
                shoot,
                game,
                request.user
            )
            state = get_game_state(game, request.user)
            data = {'shoot': shoot_result, 'state': state}
            data['dead_zone'] = dead_zone
            data['dead_ship'] = dead_ship
        else:
            raise exceptions.NotAcceptable(constants.NOT_YOUR_TURN)

        resp = serializers.ShootResultSerializer(data).data

        return Response(resp, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=True)
    def join(self, request, game_id):

        """Handles if it is possible to join to the current game"""

        game = join_game(game_id, request.user)

        if game == constants.FAIL_TO_JOIN or \
                game == constants.GAME_NOT_FOUND:
            raise exceptions.NotAcceptable(constants.FAIL_TO_JOIN)

        return Response(status=status.HTTP_202_ACCEPTED)

    @action(methods=['POST'], detail=True)
    def join_fleet(self, request, game_id):

        """After joining was accepted player sets his fleet"""

        # providing validation of joiner's fleet
        validator = validators.JoinFleetValidator(data=request.data)
        validator.is_valid(raise_exception=True)

        fleet_composition_errors = validator.check_fleet_composition()
        if fleet_composition_errors:

            return Response(
                fleet_composition_errors,
                status=status.HTTP_400_BAD_REQUEST
                )

        fleet = validator.validated_data['fleet']
        err = []
        err = join_fleet(game_id, request.user, fleet)
        if err:
            return Response({'err': err}, status=status.HTTP_400_BAD_REQUEST)
        return Response('ok', status=status.HTTP_201_CREATED)

    @action(methods=['GET'], detail=True)
    def state(self, *args, **kwargs):

        game = self.get_object()
        game.last_activity = timezone.now()
        game.save()

        self.serializer_class = serializers.StatmentGetSerializer
        serializer = self.get_serializer(game)

        return Response(serializer.data)

    @action(methods=['GET'], detail=True, url_path='initial-state')
    def initial_state(self, request, *args, **kwargs):

        game = self.get_object()

        my_bm, enemy_bm = get_game_battle_maps(game, request.user)

        my_shoots, enemy_dead_zone = [], []
        e_shoots, my_dead_zone = [], []
        my_fleet = []

        if my_bm:
            my_fleet = my_bm.fleet
            my_shoots = my_bm.shoots

        if enemy_bm:
            e_shoots = enemy_bm.shoots
            e_fleet = enemy_bm.fleet

            if e_shoots:
                e_shoots, my_dead_zone = mapped_shoots(e_shoots, my_fleet)
            if my_shoots:
                my_shoots, enemy_dead_zone = mapped_shoots(my_shoots, e_fleet)

        self.serializer_class = serializers.InitialStateSerializer
        serializer = self.get_serializer(game)

        data = serializer.data
        data['my_dead_zone'] = my_dead_zone
        data['enemy_dead_zone'] = enemy_dead_zone
        data['fleet'] = my_fleet
        data['enemy_shoots'] = e_shoots
        data['game_state'] = get_game_state(game, request.user)
        data['my_shoots'] = my_shoots
        data['current_user'] = request.user.username

        return Response(data)
