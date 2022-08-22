import datetime

from flask import Flask, abort, jsonify, request
from flask_restful import Api, Resource, reqparse, inputs
from flask_sqlalchemy import SQLAlchemy
from marshmallow import Schema, fields
import sys


app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///webcal.db'

# db part
db = SQLAlchemy(app)


class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    event = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)


db.create_all()
# end db part


class EventSchema(Schema):
    class Meta:
        ordered = True
    id = fields.Integer()
    message = fields.String()
    event = fields.String()
    date = fields.String()


# resource part
class EventToday(Resource):
    def get(self):
        event_list = Event.query.filter(Event.date == datetime.date.today()).all()
        schema = EventSchema(many=True)
        return schema.dump(event_list)


class EventResource(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument(
            'date',
            type=inputs.date,
            help="The event date with the correct format is required! The correct format is YYYY-MM-DD!",
            required=True
        )
        parser.add_argument(
            'event',
            type=str,
            help="The event name is required!",
            required=True
        )
        event = parser.parse_args()
        event["message"] = "The event has been added!"
        event['date'] = event['date'].date()

        db.session.add(Event(event=event['event'], date=event['date']))
        db.session.commit()

        return EventSchema().dump(event)

    def get(self):
        d_from = request.args.get('start_time')
        d_to = request.args.get('end_time')
        if d_from and d_to:
            event_list = Event.query.filter(Event.date >= d_from).\
                filter(Event.date <= d_to).order_by(Event.date, Event.id).all()
        else:
            event_list = Event.query.all()
        schema = EventSchema(many=True)
        return schema.dump(event_list)


class EventSpecific(Resource):
    def get(self, event_id):
        event = Event.query.filter(Event.id == event_id).first()
        if event:
            return EventSchema().dump(event)
        else:
            return abort(404, "The event doesn't exist!")

    def delete(self, event_id):
        effect = Event.query.filter(Event.id == event_id).delete()
        if effect:
            db.session.commit()
            return jsonify({"message": "The event has been deleted!"})
        else:
            return abort(404, "The event doesn't exist!")


api = Api(app)
api.add_resource(EventToday, '/event/today')
api.add_resource(EventResource, '/event')
api.add_resource(EventSpecific, '/event/<int:event_id>')

# do not change the way you run the program
if __name__ == '__main__':
    if len(sys.argv) > 1:
        arg_host, arg_port = sys.argv[1].split(':')
        app.run(host=arg_host, port=arg_port)
    else:
        app.run()
