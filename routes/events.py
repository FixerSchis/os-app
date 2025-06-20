from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_required, current_user
from models.enums import EventType, Role, TicketType
from models.event import Event
from models.event_ticket import EventTicket
from models.character import Character
from models.user import User
from models.extensions import db
from datetime import datetime, timezone
import json

from utils.email import send_event_details_updated_notification, send_event_ticket_assigned_notification_to_user, send_new_event_notification_to_all
from utils.decorators import user_admin_required

events_bp = Blueprint('events', __name__)

@events_bp.route('/')
def event_list():
    show_previous = request.args.get('show_previous', 'false').lower() == 'true'
    
    if show_previous and current_user.has_role('user_admin'):
        events = Event.query.filter(Event.end_date <= datetime.now()).order_by(Event.start_date.desc()).all()
    else:
        events = Event.query.filter(Event.end_date > datetime.now()).order_by(Event.start_date).all()
        
    return render_template('events/index.html', 
                         events=events, 
                         EventType=EventType,
                         show_previous=show_previous)

@events_bp.route('/new', methods=['GET'])
@login_required
@user_admin_required
def create_event():
    return render_template('events/edit.html', EventType=EventType)

@events_bp.route('/new', methods=['POST'])
@login_required
@user_admin_required
def create_event_post():
    event = Event(
        event_number=request.form['event_number'],
        name=request.form['name'],
        event_type=request.form['event_type'],
        description=request.form['description'],
        early_booking_deadline=datetime.strptime(request.form['early_booking_deadline'], '%Y-%m-%d'),
        start_date=datetime.strptime(request.form['start_date'], '%Y-%m-%d'),
        end_date=datetime.strptime(request.form['end_date'], '%Y-%m-%d'),
        location=request.form['location'],
        google_maps_link=request.form['google_maps_link'] if request.form['event_type'] in ['mainline', 'sanctioned'] else None,
        meal_ticket_available=bool(request.form.get('meal_ticket_available')),
        meal_ticket_price=float(request.form['meal_ticket_price']) if request.form.get('meal_ticket_available') else None,
        bunks_available=bool(request.form.get('bunks_available')),
        standard_ticket_price=float(request.form['standard_ticket_price']),
        early_booking_ticket_price=float(request.form['early_booking_ticket_price']),
        child_ticket_price_12_15=float(request.form['child_ticket_price_12_15']),
        child_ticket_price_7_11=float(request.form['child_ticket_price_7_11']),
        child_ticket_price_under_7=float(request.form['child_ticket_price_under_7'])
    )
    db.session.add(event)
    db.session.commit()
    send_new_event_notification_to_all(event)
    flash('Event created successfully!', 'success')
    return redirect(url_for('events.event_list'))

@events_bp.route('/<int:event_id>/edit', methods=['GET'])
@login_required
@user_admin_required
def edit_event(event_id):
    event = Event.query.get_or_404(event_id)
    return render_template('events/edit.html', event=event, EventType=EventType)

@events_bp.route('/<int:event_id>/edit', methods=['POST'])
@login_required
@user_admin_required
def edit_event_post(event_id):
    event = Event.query.get_or_404(event_id)
    event.event_number = request.form['event_number']
    event.name = request.form['name']
    event.event_type = request.form['event_type']
    event.description = request.form['description']
    event.early_booking_deadline = datetime.strptime(request.form['early_booking_deadline'], '%Y-%m-%d')
    event.start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d')
    event.end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d')
    event.location = request.form['location']
    event.google_maps_link = request.form['google_maps_link'] if request.form['event_type'] in ['mainline', 'sanctioned'] else None
    event.meal_ticket_available = bool(request.form.get('meal_ticket_available'))
    event.meal_ticket_price = float(request.form['meal_ticket_price']) if request.form.get('meal_ticket_available') else None
    event.bunks_available = bool(request.form.get('bunks_available'))
    event.standard_ticket_price = float(request.form['standard_ticket_price'])
    event.early_booking_ticket_price = float(request.form['early_booking_ticket_price'])
    event.child_ticket_price_12_15 = float(request.form['child_ticket_price_12_15'])
    event.child_ticket_price_7_11 = float(request.form['child_ticket_price_7_11'])
    event.child_ticket_price_under_7 = float(request.form['child_ticket_price_under_7'])
    db.session.commit()
    for ticket in event.tickets:
        send_event_details_updated_notification(ticket.character.user, event, ticket.character)
    flash('Event updated successfully!', 'success')
    return redirect(url_for('events.event_list'))

@events_bp.route('/<int:event_id>/purchase', methods=['GET'])
@login_required
def purchase_ticket(event_id):
    event = Event.query.get_or_404(event_id)
    if not current_user.has_active_character():
        flash('You need an active character to purchase tickets.', 'error')
        return redirect(url_for('events.event_list'))
    return render_template('events/purchase.html', event=event, TicketType=TicketType, EventType=EventType)

@events_bp.route('/<int:event_id>/purchase', methods=['POST'])
@login_required
def purchase_ticket_post(event_id):
    event = Event.query.get_or_404(event_id)

    cart_data = request.form.get('cart')
    if not cart_data:
        flash('No tickets in cart.', 'error')
        return redirect(url_for('events.purchase_ticket', event_id=event_id))

    try:
        cart = json.loads(cart_data)
    except Exception:
        flash('Invalid cart data.', 'error')
        return redirect(url_for('events.purchase_ticket', event_id=event_id))

    tickets_created = 0
    for item in cart:
        ticket_type = item.get('ticketType')
        meal_ticket = bool(item.get('mealTicket'))
        requires_bunk = bool(item.get('requiresBunk'))
        ticket_for = item.get('ticketFor')  # 'self' or 'other'
        character_id = None
        if ticket_for == 'self':
            if not current_user.has_active_character():
                continue
            character_id = current_user.get_active_character().id
        else:
            char_id_str = item.get('characterId')
            if not char_id_str or '.' not in char_id_str:
                continue
            user_id, player_id = char_id_str.split('.')
            try:
                user_id = int(user_id)
                player_id = int(player_id)
            except ValueError:
                continue
            character = Character.query.filter_by(user_id=user_id, player_id=player_id).first()
            if not character:
                continue
            character_id = character.id

        character = Character.query.get_or_404(character_id)

        # Crew ticket permission check
        if ticket_type == 'crew' and not current_user.has_any_role([Role.USER_ADMIN.value, Role.RULES_TEAM.value, Role.PLOT_TEAM.value, Role.NPC.value]):
            continue

        price_paid = float(item.get('price', 0))
        # Check for existing ticket
        ticket = EventTicket.query.filter_by(event_id=event_id, character_id=character_id).first()
        if ticket:
            ticket.ticket_type = ticket_type
            ticket.meal_ticket = meal_ticket
            ticket.requires_bunk = requires_bunk
            ticket.price_paid += price_paid
            ticket.assigned_by_id = current_user.id
            ticket.assigned_at = datetime.utcnow()
        else:
            ticket = EventTicket(
                event_id=event_id,
                character_id=character_id,
                ticket_type=ticket_type,
                meal_ticket=meal_ticket,
                requires_bunk=requires_bunk,
                price_paid=price_paid,
                assigned_by_id=current_user.id,
                assigned_at=datetime.utcnow()
            )
            db.session.add(ticket)
            send_event_ticket_assigned_notification_to_user(character.user, ticket, event, character)
        tickets_created += 1

    db.session.commit()
    if tickets_created:
        flash(f'{tickets_created} ticket(s) purchased successfully!', 'success')
    else:
        flash('No tickets were purchased.', 'error')
    return redirect(url_for('events.event_list'))

@events_bp.route('/<int:event_id>/assign', methods=['GET'])
@login_required
@user_admin_required
def assign_ticket(event_id):
    event = Event.query.get_or_404(event_id)
    return render_template('events/assign.html', event=event, TicketType=TicketType)

@events_bp.route('/<int:event_id>/assign', methods=['POST'])
@login_required
@user_admin_required
def assign_ticket_post(event_id):
    event = Event.query.get_or_404(event_id)
    user_id, character_id = request.form['character'].split('.')
    character = Character.query.filter_by(user_id=user_id, character_id=character_id).first_or_404()
    
    ticket_type = request.form['ticket_type']
    price_paid = 0 if ticket_type == 'crew' else float(request.form['price_paid'])
    
    ticket = EventTicket.query.filter_by(event_id=event_id, character_id=character.id).first()
    if ticket:
        ticket.ticket_type = ticket_type
        ticket.meal_ticket = bool(request.form.get('meal_ticket'))
        ticket.requires_bunk = bool(request.form.get('requires_bunk'))
        ticket.price_paid = price_paid
        ticket.assigned_by_id = current_user.id
        ticket.assigned_at = datetime.utcnow()
    else:
        ticket = EventTicket(
            event_id=event_id,
            character_id=character.id,
            ticket_type=ticket_type,
            meal_ticket=bool(request.form.get('meal_ticket')),
            requires_bunk=bool(request.form.get('requires_bunk')),
            price_paid=price_paid,
            assigned_by_id=current_user.id,
            assigned_at=datetime.utcnow()
        )
        db.session.add(ticket)
        send_event_ticket_assigned_notification_to_user(character.user, ticket, event, character)
    db.session.commit()
    flash('Ticket assigned successfully!', 'success')
    return redirect(url_for('events.view_attendees', event_id=event_id))

@events_bp.route('/<int:event_id>/attendees', methods=['GET'])
@login_required
@user_admin_required
def view_attendees(event_id):
    event = Event.query.get_or_404(event_id)
    tickets = (
        EventTicket.query
        .filter_by(event_id=event_id)
        .join(EventTicket.character)
        .join(Character.user)
        .add_entity(Character)
        .add_entity(User)
        .all()
    )
    return render_template('events/attendees.html', event=event, tickets=tickets, TicketType=TicketType)

@events_bp.route('/api/get_character_ticket')
@login_required
def get_character_ticket():
    event_id = request.args.get('event_id')
    char_id_str = request.args.get('character_id')
    if not event_id or not char_id_str or '.' not in char_id_str:
        return jsonify({'success': False, 'error': 'Missing or invalid parameters'}), 400
    user_id, character_id = char_id_str.split('.')
    character = Character.query.filter_by(user_id=user_id, character_id=character_id).first()
    if not character:
        return jsonify({'success': False, 'error': 'Character not found'}), 404
    ticket = EventTicket.query.filter_by(event_id=event_id, character_id=character.id).first()
    if not ticket:
        return jsonify({'success': True, 'ticket': None})
    return jsonify({'success': True, 'ticket': {
        'ticket_type': ticket.ticket_type.value if hasattr(ticket.ticket_type, 'value') else ticket.ticket_type,
        'meal_ticket': ticket.meal_ticket,
        'requires_bunk': getattr(ticket, 'requires_bunk', False),
        'price_paid': ticket.price_paid
    }})

@events_bp.route('/api/events')
@login_required
def get_events():
    """Get list of events with optional filters."""
    # Get filter parameters
    has_started = request.args.get('has_started', type=lambda v: v.lower() == 'true')
    has_finished = request.args.get('has_finished', type=lambda v: v.lower() == 'true')
    early_booking_available = request.args.get('early_booking_available', type=lambda v: v.lower() == 'true')
    has_downtime = request.args.get('has_downtime', type=lambda v: v.lower() == 'true')
    event_type = request.args.get('event_type')
    
    # Start with base query
    query = Event.query
    
    # Apply filters
    if has_started is not None:
        if has_started:
            query = query.filter(Event.start_date <= datetime.now())
            
    if has_finished is not None:
        if has_finished:
            query = query.filter(Event.end_date <= datetime.now())
            
    if early_booking_available is not None:
        if early_booking_available:
            query = query.filter(Event.early_booking_deadline > datetime.now())
            
    if has_downtime is not None:
        from models.downtime import DowntimePeriod
        if has_downtime:
            query = query.filter(Event.id.in_(
                db.session.query(DowntimePeriod.event_id)
                .filter(DowntimePeriod.event_id.isnot(None))
            ))
    
    if event_type:
        query = query.filter(Event.event_type == event_type)
    
    # Order by end date descending
    events = query.order_by(Event.end_date.desc()).all()
    
    return jsonify({
        'events': [{
            'id': event.id,
            'event_number': event.event_number,
            'name': event.name,
            'start_date': event.start_date.strftime('%Y-%m-%d'),
            'end_date': event.end_date.strftime('%Y-%m-%d'),
            'early_booking_deadline': event.early_booking_deadline.strftime('%Y-%m-%d'),
            'event_type': event.event_type.value
        } for event in events]
    }) 