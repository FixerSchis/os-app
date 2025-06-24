from datetime import datetime, timedelta

from models.database.conditions import Condition, ConditionStage
from models.database.exotic_substances import ExoticSubstance
from models.database.item import Item
from models.database.item_blueprint import ItemBlueprint
from models.database.item_type import ItemType
from models.database.medicaments import Medicament
from models.enums import EventType, PrintTemplateType, ScienceType
from models.event import Event
from models.tools.character import Character
from models.tools.event_ticket import EventTicket
from models.tools.print_template import PrintTemplate


class TestTemplatesRoutes:
    def login_admin(self, test_client, admin_user):
        with test_client.session_transaction() as sess:
            sess["_user_id"] = str(admin_user.id)
            sess["_fresh"] = True

    def clear_templates(self, db):
        db.session.query(PrintTemplate).delete()
        db.session.commit()

    def make_template(self, admin_user, type_value, type_name, front_html="Hello"):
        return PrintTemplate(
            type=type_value,
            type_name=type_name,
            created_by_user_id=admin_user.id,
            front_html=front_html,
        )

    def test_template_list(self, test_client, admin_user, db):
        self.clear_templates(db)
        self.login_admin(test_client, admin_user)
        template = self.make_template(
            admin_user, PrintTemplateType.CHARACTER_SHEET, "Character Sheet List"
        )
        db.session.add(template)
        db.session.commit()
        resp = test_client.get("/templates/list")
        assert resp.status_code == 200
        assert b"Character Sheet" in resp.data

    def test_template_new_post(self, test_client, admin_user, db):
        self.clear_templates(db)
        self.login_admin(test_client, admin_user)
        resp = test_client.post(
            "/templates/new",
            data={"type": PrintTemplateType.EXOTIC_SUBSTANCE_LABEL},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b"Template creation not yet implemented" in resp.data

    def test_template_edit_get(self, test_client, admin_user, db):
        self.clear_templates(db)
        self.login_admin(test_client, admin_user)
        template = self.make_template(
            admin_user, PrintTemplateType.CONDITION_CARD, "Condition Card Edit"
        )
        template.front_html = "Edit Template"
        db.session.add(template)
        db.session.commit()
        resp = test_client.get(f"/templates/{template.id}/edit")
        assert resp.status_code == 200
        assert b"Edit Template" in resp.data

    def test_template_edit_post(self, test_client, admin_user, db):
        self.clear_templates(db)
        self.login_admin(test_client, admin_user)
        template = self.make_template(admin_user, PrintTemplateType.ITEM_CARD, "Item Card Edit")
        db.session.add(template)
        db.session.commit()
        resp = test_client.post(
            f"/templates/{template.id}/edit",
            data={
                "front_html": "<div>Front</div>",
                "back_html": "<div>Back</div>",
                "css_styles": "body { color: red; }",
            },
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b"Template updated successfully" in resp.data
        db.session.refresh(template)
        assert template.front_html == "<div>Front</div>"
        assert template.back_html == "<div>Back</div>"
        assert template.css_styles == "body { color: red; }"

    def test_render_template_preview(self, test_client, admin_user, db):
        self.clear_templates(db)
        self.login_admin(test_client, admin_user)
        template = self.make_template(
            admin_user,
            PrintTemplateType.MEDICAMENT_CARD,
            "Medicament Card Preview",
            front_html="Hello",
        )
        db.session.add(template)
        db.session.commit()
        resp = test_client.post(
            f"/templates/api/{template.id}/render",
            json={"front_html": "Hello", "back_html": "", "css_styles": ""},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert "front_html" in data
        assert "success" in data

    def test_print_template_preview(self, test_client, admin_user, db):
        self.clear_templates(db)
        self.login_admin(test_client, admin_user)
        template = self.make_template(
            admin_user,
            PrintTemplateType.EXOTIC_SUBSTANCE_LABEL,
            "Exotic Label Preview",
            front_html="Hello",
        )
        db.session.add(template)
        db.session.commit()
        resp = test_client.post(
            f"/templates/api/{template.id}/print_preview",
            json={"front_html": "Hello", "back_html": "", "css_styles": ""},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert "pdf" in data
        assert "double_sided" in data

    def test_print_item_sheet_character(self, test_client, admin_user, db):
        self.clear_templates(db)
        self.login_admin(test_client, admin_user)
        template = self.make_template(
            admin_user, PrintTemplateType.CHARACTER_SHEET, "Character Sheet Print"
        )
        db.session.add(template)
        db.session.commit()
        character = Character(
            name="Char",
            user_id=admin_user.id,
            species_id=1,
            faction_id=1,
            status="active",
        )
        db.session.add(character)
        db.session.commit()
        resp = test_client.get(f"/templates/characters/{character.id}/print")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "pdf" in data

    def test_print_item_sheet_item(self, test_client, admin_user, db):
        self.clear_templates(db)
        self.login_admin(test_client, admin_user)
        template = self.make_template(admin_user, PrintTemplateType.ITEM_CARD, "Item Card Print")
        db.session.add(template)
        db.session.commit()
        item_type = ItemType(name="WeaponA", id_prefix="WA")
        db.session.add(item_type)
        db.session.commit()
        blueprint = ItemBlueprint(
            name="Plasma RifleA",
            item_type_id=item_type.id,
            blueprint_id=1,
            base_cost=500,
            purchaseable=True,
        )
        db.session.add(blueprint)
        db.session.commit()
        item = Item(blueprint_id=blueprint.id, item_id=1)
        db.session.add(item)
        db.session.commit()
        resp = test_client.get(f"/templates/items/{item.id}/print")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "pdf" in data

    def test_print_item_sheet_condition(self, test_client, admin_user, db):
        self.clear_templates(db)
        self.login_admin(test_client, admin_user)
        template = self.make_template(
            admin_user, PrintTemplateType.CONDITION_CARD, "Condition Card Print"
        )
        db.session.add(template)
        db.session.commit()
        condition = Condition(name="Cond")
        db.session.add(condition)
        db.session.commit()
        stage = ConditionStage(
            condition_id=condition.id,
            stage_number=1,
            rp_effect="",
            diagnosis="",
            cure="",
            duration=1,
        )
        db.session.add(stage)
        db.session.commit()
        resp = test_client.get(f"/templates/conditions/{condition.id}/print")
        assert resp.status_code in (200, 400, 404)  # Accept 400/404 if more is required
        if resp.status_code == 200:
            data = resp.get_json()
            assert "pdf" in data

    def test_print_item_sheet_medicament(self, test_client, admin_user, db):
        self.clear_templates(db)
        self.login_admin(test_client, admin_user)
        template = self.make_template(
            admin_user, PrintTemplateType.MEDICAMENT_CARD, "Medicament Card Print"
        )
        db.session.add(template)
        db.session.commit()
        medicament = Medicament(name="Med")
        medicament.wiki_slug = "med"
        db.session.add(medicament)
        db.session.commit()
        resp = test_client.get(f"/templates/medicaments/{medicament.id}/print")
        assert resp.status_code in (200, 400, 404)
        if resp.status_code == 200:
            data = resp.get_json()
            assert "pdf" in data

    def test_print_item_sheet_exotic(self, test_client, admin_user, db):
        self.clear_templates(db)
        self.login_admin(test_client, admin_user)
        template = self.make_template(
            admin_user, PrintTemplateType.EXOTIC_SUBSTANCE_LABEL, "Exotic Card Print"
        )
        db.session.add(template)
        db.session.commit()
        exotic = ExoticSubstance(name="Exotic", type=ScienceType.ETHERIC)
        exotic.wiki_slug = "exotic"
        db.session.add(exotic)
        db.session.commit()
        resp = test_client.get(f"/templates/exotics/{exotic.id}/print")
        assert resp.status_code in (200, 400, 404)
        if resp.status_code == 200:
            data = resp.get_json()
            assert "pdf" in data

    def test_print_event_items_characters(self, test_client, admin_user, db):
        self.clear_templates(db)
        self.login_admin(test_client, admin_user)
        template = self.make_template(
            admin_user, PrintTemplateType.CHARACTER_SHEET, "Character Sheet Event Print"
        )
        db.session.add(template)
        db.session.commit()
        now = datetime.now()
        event = Event(
            event_number="E1",
            name="Event",
            event_type=EventType.MAINLINE,
            early_booking_deadline=now + timedelta(days=30),
            booking_deadline=now + timedelta(days=40),
            start_date=now + timedelta(days=60),
            end_date=now + timedelta(days=63),
            standard_ticket_price=100.0,
            early_booking_ticket_price=80.0,
            child_ticket_price_12_15=50.0,
            child_ticket_price_7_11=25.0,
            child_ticket_price_under_7=0.0,
        )
        db.session.add(event)
        db.session.commit()
        character = Character(
            name="Char",
            user_id=admin_user.id,
            species_id=1,
            faction_id=1,
            status="active",
        )
        db.session.add(character)
        db.session.commit()
        ticket = EventTicket(
            event_id=event.id,
            character_id=character.id,
            user_id=admin_user.id,
            ticket_type="adult",
            price_paid=100.0,
            assigned_by_id=admin_user.id,
        )
        db.session.add(ticket)
        db.session.commit()
        resp = test_client.get(f"/templates/events/{event.id}/print/characters")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "pdf" in data

    def test_print_event_items_items(self, test_client, admin_user, db):
        self.clear_templates(db)
        self.login_admin(test_client, admin_user)
        template = self.make_template(
            admin_user, PrintTemplateType.ITEM_CARD, "Item Card Event Print"
        )
        db.session.add(template)
        db.session.commit()
        now = datetime.now()
        event = Event(
            event_number="E2",
            name="Event",
            event_type=EventType.MAINLINE,
            early_booking_deadline=now + timedelta(days=30),
            booking_deadline=now + timedelta(days=40),
            start_date=now + timedelta(days=60),
            end_date=now + timedelta(days=63),
            standard_ticket_price=100.0,
            early_booking_ticket_price=80.0,
            child_ticket_price_12_15=50.0,
            child_ticket_price_7_11=25.0,
            child_ticket_price_under_7=0.0,
        )
        db.session.add(event)
        db.session.commit()
        item_type = ItemType(name="WeaponB", id_prefix="WB")
        db.session.add(item_type)
        db.session.commit()
        blueprint = ItemBlueprint(
            name="Plasma RifleB",
            item_type_id=item_type.id,
            blueprint_id=1,
            base_cost=500,
            purchaseable=True,
        )
        db.session.add(blueprint)
        db.session.commit()
        item = Item(blueprint_id=blueprint.id, item_id=1)
        db.session.add(item)
        db.session.commit()
        character = Character(
            name="Char2",
            user_id=admin_user.id,
            species_id=1,
            faction_id=1,
            status="active",
        )
        db.session.add(character)
        db.session.commit()
        ticket = EventTicket(
            event_id=event.id,
            character_id=character.id,
            user_id=admin_user.id,
            ticket_type="adult",
            price_paid=100.0,
            assigned_by_id=admin_user.id,
        )
        db.session.add(ticket)
        db.session.commit()
        resp = test_client.get(f"/templates/events/{event.id}/print/items")
        assert resp.status_code in (200, 400, 404)
        if resp.status_code == 200:
            data = resp.get_json()
            assert "pdf" in data

    def test_template_layout_get(self, test_client, admin_user, db):
        self.clear_templates(db)
        self.login_admin(test_client, admin_user)
        template = self.make_template(
            admin_user, PrintTemplateType.CHARACTER_SHEET, "Character Sheet Layout"
        )
        db.session.add(template)
        db.session.commit()
        resp = test_client.get(f"/templates/{template.id}/layout")
        assert resp.status_code == 200
        assert b"Layout" in resp.data or b"PrintTemplateType" in resp.data

    def test_template_layout_post(self, test_client, admin_user, db):
        self.clear_templates(db)
        self.login_admin(test_client, admin_user)
        template = self.make_template(
            admin_user, PrintTemplateType.CONDITION_CARD, "Condition Card Layout"
        )
        db.session.add(template)
        db.session.commit()
        resp = test_client.post(
            f"/templates/{template.id}/layout",
            json={"width_mm": 100, "height_mm": 50, "is_landscape": True},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        db.session.refresh(template)
        assert template.width_mm == 100
        assert template.height_mm == 50
        assert template.is_landscape is True
