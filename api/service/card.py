import json
import typing
from werkzeug.exceptions import Forbidden
from marshmallow.exceptions import ValidationError
import sqlalchemy as sqla

from api.app import db
from api.model import BoardPermission, CardActivityEvent
from api.model.board import BoardAllowedUser

from api.model.user import User
from api.model.list import BoardList
from api.model.card import (
    Card, CardActivity, CardComment
)


def get_card(current_user: User, card_id: int) -> Card:
    """Gets card if user can access the board
    Args:
        current_user (User): Current user
        card_id (int): Card ID:
    Returns:
        Card: Card ORM object.
    """
    card = Card.get_or_404(card_id)
    if card.board.is_user_can_access(current_user.id):
        return card
    raise Forbidden()


def get_cards(current_user: User, board_list: BoardList) -> typing.List[Card]:
    """Gets cards from board list

    Args:
        current_user (User): Logged in user
        board_list (BoardList): Board list

    Returns:
        typing.List[Card]: List of cards
    """
    if (
        board_list.board.is_user_can_access(current_user.id)
    ):
        return board_list.cards
    raise Forbidden()


def post_card(current_user: User, board_list: BoardList, data: dict) -> Card:
    """Creates a card.

    Args:
        current_user (User): Logged in user
        board_list (BoardList): Board list

    Raises:
        Forbidden: Don't have permission to create card

    Returns:
        Card: Card ORM object
    """
    if (
        board_list.board.has_permission(
            current_user.id, BoardPermission.CARD_EDIT
        )
    ):
        card = Card(
            **data,
            owner_id=current_user.id,
            board_id=board_list.board_id,
            list_id=board_list.id,
        )
        position_max = db.engine.execute(
            f"SELECT MAX(position) FROM card WHERE list_id={board_list.id}"
        ).fetchone()
        if position_max[0] is not None:
            card.position = position_max[0] + 1
        return card
    raise Forbidden()


def patch_card(current_user: User, card: Card, data: dict) -> Card:
    """Updates a card

    Args:
        current_user (User): Logged in user
        card (Card): Card ORM object to update
        data (dict): Update data

    Raises:
        Forbidden: Don't have permission to update card

    Returns:
        Card: Updated card ORM object
    """
    if (
        card.board.has_permission(
            current_user.id, BoardPermission.CARD_EDIT
        )
    ):
        for key, value in data.items():
            if key == "list_id" and card.list_id != value:
                # Get target list id
                target_list: BoardList = BoardList.get_or_404(value)

                if target_list.board_id != card.board_id:
                    raise ValidationError(
                        {"list_id": ["Cannot move card to other board!"]})

                activity = CardActivity(
                    user_id=current_user.id,
                    event=CardActivityEvent.CARD_MOVE_TO_LIST.value,
                    entity_id=card.id,
                    changes=json.dumps(
                        {
                            "from": {
                                "id": card.list_id,
                                "title": card.board_list.title
                            },
                            "to": {
                                "id": value,
                                "title": target_list.title
                            }
                        }
                    )
                )
                card.activities.append(activity)
                card.list_id = value
            elif hasattr(card, key):
                setattr(card, key, value)
        return card
    raise Forbidden()


def post_card_comment(
    current_user: User, card: Card, data: dict
) -> CardActivity:
    if (
        card.board.has_permission(
            current_user.id, BoardPermission.CARD_COMMENT
        )
    ):
        comment = CardComment(
            user_id=current_user.id,
            board_id=card.board_id,
            **data
        )
        activity = CardActivity(
            user_id=current_user.id,
            event=CardActivityEvent.CARD_COMMENT.value,
            entity_id=comment.id,
            comment=comment
        )
        card.activities.append(activity)
        return activity
    raise Forbidden()


def patch_card_comment(
    current_user: User, comment: CardComment, data: dict
) -> CardComment:
    user_can_edit = (
        comment.user_id == current_user.id and
        comment.board.has_permission(
            current_user.id,
            BoardPermission.CARD_COMMENT
        )
    )
    if (user_can_edit):
        comment.update(**data)
        comment.card.activities.append(
            CardActivity(
                user_id=current_user.id,
                event=CardActivityEvent.CARD_COMMENT.value,
                entity_id=comment.id
            )
        )


def delete_card_comment(current_user: User, comment: CardComment):
    user_can_delete = (
        comment.user_id == current_user.id and
        comment.card.board_list.board.is_user_can_access(current_user.id)
    )

    if (user_can_delete):
        comment.delete()
    else:
        raise Forbidden()


def delete_card(current_user: User, card: Card):
    """Deletes a card.

    Args:
        current_user (User): Logged in user
        card (Card): Card ORM object  to delete

    Raises:
        Forbidden: Don't have permission to delete card
    """
    if (
        card.board_list.board.has_permission(
            current_user.id, BoardPermission.CARD_EDIT
        )
    ):
        db.session.delete(card)
    else:
        raise Forbidden()


def get_card_activities(current_user: User, card: Card, args: dict = {}):
    if not card.board.is_user_can_access(current_user.id):
        raise Forbidden()

    # Query and paginate
    query = CardActivity.query.filter(CardActivity.card_id == card.id)
    # Checks type
    if args["type"] == "comment":
        query = query.filter(CardActivity.event ==
                             CardActivityEvent.CARD_COMMENT.value)

    # Sortby
    sortby = args.get("sort_by", "activity_on")
    order = args.get("order", "desc")

    if not hasattr(CardActivity, sortby):
        sortby = "activity_on"

    if order == "asc":
        query = query.order_by(sqla.asc(getattr(CardActivity, sortby)))
    elif order == "desc":
        query = query.order_by(sqla.desc(getattr(CardActivity, sortby)))

    return query.paginate(args["page"], args["per_page"])


def assign_card_member(
    current_user: User, card: Card, board_member: BoardAllowedUser
):
    if (
        card.board.has_permission(
            current_user.id, BoardPermission.CARD_ASSIGN_MEMBER)
    ):
        pass

    raise Forbidden()
