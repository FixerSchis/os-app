import pytest
from models.tools.downtime import DowntimePeriod, DowntimePack
from models.enums import DowntimeStatus, DowntimeTaskStatus

def test_new_downtime_period_with_pack(db, character):
    """Test creation of a new DowntimePeriod with a DowntimePack."""
    # First create an event
    from models.event import Event
    from datetime import datetime, timedelta
    
    now = datetime.now()
    early_deadline = now + timedelta(days=30)
    start_date = now + timedelta(days=60)
    end_date = now + timedelta(days=63)
    
    event = Event(
        event_number="EV003",
        name="Test Event 3",
        event_type="mainline",
        early_booking_deadline=early_deadline,
        start_date=start_date,
        end_date=end_date,
        standard_ticket_price=100.0,
        early_booking_ticket_price=80.0,
        child_ticket_price_12_15=50.0,
        child_ticket_price_7_11=25.0,
        child_ticket_price_under_7=0.0
    )
    db.session.add(event)
    db.session.commit()
    
    # Create the downtime period
    period = DowntimePeriod(
        status=DowntimeStatus.PENDING,
        event_id=event.id
    )
    
    db.session.add(period)
    db.session.commit()
    
    # Create a downtime pack
    pack = DowntimePack(
        period_id=period.id,
        character_id=character.id,
        status=DowntimeTaskStatus.ENTER_PACK,
        energy_credits=100,
        items=[{"id": 1, "quantity": 2}],
        exotic_substances=[{"id": 1, "quantity": 1}],
        conditions=[{"id": 1, "stage": 1}],
        samples=[{"id": 1}],
        cybernetics=[{"id": 1}],
        research_teams=[1, 2],
        purchases=[{"item_id": 1, "quantity": 1}],
        modifications=[{"item_id": 1, "mod_id": 1}],
        engineering=[{"task": "repair", "item_id": 1}],
        science=[{"task": "analyze", "sample_id": 1}],
        research=[{"task": "invent", "blueprint_id": 1}],
        reputation=[{"faction_id": 1, "change": 5}],
        review_data={"notes": "Test review"}
    )
    
    db.session.add(pack)
    db.session.commit()
    
    # Retrieve and assert
    retrieved_period = DowntimePeriod.query.get(period.id)
    
    assert retrieved_period is not None
    assert retrieved_period.status == DowntimeStatus.PENDING
    assert retrieved_period.event_id == event.id
    
    # Check packs relationship
    assert len(retrieved_period.packs) == 1
    retrieved_pack = retrieved_period.packs[0]
    
    assert retrieved_pack.period_id == period.id
    assert retrieved_pack.character_id == character.id
    assert retrieved_pack.status == DowntimeTaskStatus.ENTER_PACK
    assert retrieved_pack.energy_credits == 100
    assert retrieved_pack.items == [{"id": 1, "quantity": 2}]
    assert retrieved_pack.exotic_substances == [{"id": 1, "quantity": 1}]
    assert retrieved_pack.conditions == [{"id": 1, "stage": 1}]
    assert retrieved_pack.samples == [{"id": 1}]
    assert retrieved_pack.cybernetics == [{"id": 1}]
    assert retrieved_pack.research_teams == [1, 2]
    assert retrieved_pack.purchases == [{"item_id": 1, "quantity": 1}]
    assert retrieved_pack.modifications == [{"item_id": 1, "mod_id": 1}]
    assert retrieved_pack.engineering == [{"task": "repair", "item_id": 1}]
    assert retrieved_pack.science == [{"task": "analyze", "sample_id": 1}]
    assert retrieved_pack.research == [{"task": "invent", "blueprint_id": 1}]
    assert retrieved_pack.reputation == [{"faction_id": 1, "change": 5}]
    assert retrieved_pack.review_data == {"notes": "Test review"}
    
    # Test to_dict methods
    period_dict = retrieved_period.to_dict()
    assert period_dict['status'] == DowntimeStatus.PENDING.value
    assert period_dict['event_id'] == event.id
    
    pack_dict = retrieved_pack.to_dict()
    assert pack_dict['character_id'] == character.id
    assert pack_dict['energy_credits'] == 100 
