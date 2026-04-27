from marshmallow import Schema, EXCLUDE, fields


class PageMetaSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    total_elements = fields.Integer()
    page = fields.Integer()
    per_page = fields.Integer()
