import copy 
import typing

from marshmallow import (Schema, ValidationError,
                         fields, validate, validates_schema, EXCLUDE)
from marshmallow_sqlalchemy import SQLAlchemySchema
from marshmallow_sqlalchemy.fields import Nested

from api.model.board import Board
from api.model.card import Card, CardActivity, CardComment, CardListChange
from api.model.list import BoardList
from ..model import CardActivityEvent, user


class ResetPasswordSchema(Schema):
    reset_token = fields.String(required=True, load_only=True)
    password = fields.String(required=True, load_only=True)


class UserSchema(SQLAlchemySchema):

    id = fields.Integer(dump_only=True)
    username = fields.String(validate=validate.Length(3, 255), required=True)
    name = fields.String()
    avatar_url = fields.String()
    password = fields.String(
        validate=validate.Length(3, 255), required=True, load_only=True)
    current_password = fields.String(
        validate=validate.Length(3, 255), required=True, load_only=True)

    email = fields.Email(required=True)
    full_name = fields.String(
        validate=validate.Length(max=255), required=False)

    registered_date = fields.DateTime(dump_only=True)

    current_login_at = fields.DateTime(dump_only=True)
    current_login_ip = fields.String(dump_only=True)
    last_login_at = fields.DateTime(dump_only=True)
    last_login_ip = fields.String(dump_only=True)

    # TODO Need a vaildator for this!
    timezone = fields.String()
    roles = fields.Method("get_roles", "get_roles_deserialize")

    def get_roles(self, data):
        return [role.name for role in data.roles]

    def get_roles_deserialize(self, obj):
        return obj

    @validates_schema
    def validate_schema(self, data, **kwargs):
        errors = {}
        # Check if user exists
        if "username" in data.keys():
            q = user.User.query.filter(
                user.User.username == data["username"])

            if self.instance:
                q = q.filter(user.User.id != self.instance.id)
            if q.first():
                errors["username"] = ["Username already taken."]
        if "email" in data.keys():
            q = user.User.query.filter(user.User.email == data["email"])

            if self.instance:
                q = q.filter(user.User.id != self.instance.id)

            if q.first():
                errors["email"] = ["Email already taken."]
        if "current_password" in data.keys():
            if not self.instance.check_password(data["current_password"]):
                errors["current_password"] = ["Invalid current password"]

        if len(errors.keys()) > 0:
            raise ValidationError(errors)

    class Meta:
        model = user.User


class CardMemberSchema(SQLAlchemySchema):
    id = fields.Integer(dump_only=True)
    # activity_id = fields.Integer(dump_only=True)
    user_id = fields.Integer(dump_only=True)
    send_notification = fields.Boolean(required=True)

    user = fields.Nested(
        UserSchema(only=("name", "email", "avatar_url", "username",)),
        dump_only=True
    )


class CardCommentSchema(SQLAlchemySchema):
    id = fields.Integer(dump_only=True)
    user_id = fields.Integer(dump_only=True)
    # activity_id = fields.Integer(dump_only=True, required=True)
    comment = fields.String(required=True)

    created = fields.DateTime(dump_only=True)
    updated = fields.DateTime(dump_only=True)

    class Meta:
        model = CardComment


class CardListChangeSchema(SQLAlchemySchema):
    id = fields.Integer(dump_only=True)
    # activity_id = fields.Integer(dump_only=True)
    from_list_id = fields.Integer(dump_only=True)
    to_list_id = fields.Integer(dump_only=True)

    # FIXME: This just a workaround to get boardlist, find better solution!
    from_list = fields.Nested(
        Schema.from_dict({"title": fields.String(dump_only=True)}))
    to_list = fields.Nested(
        Schema.from_dict({"title": fields.String(dump_only=True)}))

    class Meta:
        model = CardListChange


class CardActivitySchema(SQLAlchemySchema):
    id = fields.Integer(dump_only=True)
    card_id = fields.Integer()
    user_id = fields.Integer()
    activity_on = fields.DateTime("%Y-%m-%d %H:%M:%S")
    entity_id = fields.Integer()
    event = fields.Integer(dump_only=True)

    comment = fields.Nested(CardCommentSchema, dump_only=True)
    member = fields.Nested(CardMemberSchema, dump_only=True)

    user = fields.Nested(
        UserSchema(only=("name", "email", "avatar_url", "username",)),
        dump_only=True
    )
    list_change = Nested(CardListChangeSchema, dump_only=True)

    def remove_fields(self, exclude: typing.Tuple):
        """Removes fields from schema to prevent unnecessary SQL calls"""
        for i in exclude:
            self.dump_fields.pop(i, None)
            self.fields.pop(i, None)
            self.load_fields.pop(i, None)

    def dump(
        self,
        obj: typing.Union[typing.List[CardActivity], CardActivity],
        *,
        many: typing.Union[bool, None] = None
    ):
        """
        Dumps relationship based on event.
        Prevents marshmallow-sqlalchemy doing unnecessary SQL calls.
        """
        original_dump = copy.deepcopy(self.dump_fields)
        original_fields = copy.deepcopy(self.fields)
        original_load_fields = copy.deepcopy(self.load_fields)
        retval = None
        if many:
            retval = []
            for entry in obj:
                # Reload original stuff before removing anything.
                self.dump_fields = copy.deepcopy(original_dump)
                self.fields = copy.deepcopy(original_fields)
                self.load_fields = copy.deepcopy(original_load_fields)

                if entry.event == CardActivityEvent.CARD_COMMENT.value:
                    self.remove_fields(("member", "list_change",))
                elif entry.event == CardActivityEvent.CARD_MOVE_TO_LIST.value:
                    self.remove_fields(("member", "comment",))
                retval.append(super().dump(entry, many=False))
        else:
            retval = super().dump(obj, many=False)

        self.dump_fields = copy.deepcopy(original_dump)
        self.fields = copy.deepcopy(original_fields)
        self.load_fields = copy.deepcopy(original_load_fields)
        return retval


class CardSchema(SQLAlchemySchema):
    id = fields.Integer(dump_only=True)
    list_id = fields.Integer()
    owner_id = fields.Integer(dump_only=True)

    title = fields.String(required=True)
    description = fields.String()
    due_date = fields.DateTime(required=False)
    position = fields.Integer()

    class Meta:
        model = Card
        unknown = EXCLUDE


class BoardListSchema(SQLAlchemySchema):

    id = fields.Integer(dump_only=True)
    board_id = fields.Integer()
    title = fields.String(required=True)
    position = fields.Integer(required=True)

    cards = fields.Nested(
        CardSchema,
        many=True,
        only=("id", "title", "position",),
        dump_only=True
    )

    class Meta:
        model = BoardList
        unknown = EXCLUDE


class BoardSchema(SQLAlchemySchema):

    id = fields.Integer(dump_only=True)
    owner_id = fields.Integer()
    title = fields.String(required=True)
    lists = fields.Nested(BoardListSchema, many=True, dump_only=True)
    background_image = fields.String()
    background_color = fields.String()

    class Meta:
        model = Board
