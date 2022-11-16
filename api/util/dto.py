from api.util import schemas


class CardDTO:
    card_schema = schemas.CardSchema()
    comment_schema = schemas.CardCommentSchema()

    activity_schema = schemas.CardActivitySchema()
    activity_paginated_schema = schemas.CardActivityPaginatedSchema()
    activity_schema_query = schemas.CardActivityQuerySchema()

    member_schema = schemas.CardMemberSchema()
    date_schema = schemas.CardDateSchema()
    query_schema = schemas.CardQuerySchema()


class SIODTO:
    event_schema = schemas.SIOEventSchema()
    delete_event_scehma = schemas.SIODeleteEventSchema()
