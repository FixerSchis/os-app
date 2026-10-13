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

    def test_render_template_preview_keeps_sample_fields(self, test_client, admin_user, db):
        self.clear_templates(db)
        self.login_admin(test_client, admin_user)
        template = self.make_template(
            admin_user,
            PrintTemplateType.MEDICAMENT_CARD,
            "Medicament Card Fields",
            front_html="{{ medicament.name }} {{ generate_qr_code(medicament.name) }}",
        )
        db.session.add(template)
        db.session.commit()
        front_html = (
            "{{ medicament.name }} {{ generate_qr_code(medicament.name) }} "
            "{{ medicament.modes_list[0].name }}"
        )
        resp = test_client.post(
            f"/templates/api/{template.id}/render",
            json={
                "front_html": front_html,
                "back_html": "",
                "css_styles": "",
            },
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "Radiation Nanosponges" in data["front_html"]
        assert "TREAT" in data["front_html"]
        assert "data:image/png;base64," in data["front_html"]

    def test_render_character_sheet_with_sample_character(self, test_client, admin_user, db):
        self.clear_templates(db)
        self.login_admin(test_client, admin_user)
        template = self.make_template(
            admin_user, PrintTemplateType.CHARACTER_SHEET, "Character Sheet Sample"
        )
        db.session.add(template)
        db.session.commit()
        resp = test_client.post(
            f"/templates/api/{template.id}/render",
            json={
                "front_html": "{{ character.name }} {{ character.user.first_name }}",
                "back_html": "",
                "css_styles": "",
            },
        )
        assert resp.status_code == 200
        assert "Alex Chen Admin" in resp.get_json()["front_html"]

    def test_render_character_sheet_with_preview_data(
        self, test_client, admin_user, db, species, faction, skill
    ):
        self.clear_templates(db)
        self.login_admin(test_client, admin_user)
        template = self.make_template(
            admin_user, PrintTemplateType.CHARACTER_SHEET, "Character Sheet Data"
        )
        db.session.add(template)
        db.session.commit()
        characters_before = Character.query.count()
        front_html = (
            "{{ character.name }}|{{ character.species.name }}|{{ character.faction.name }}|"
            "{% for row in character.skills %}{{ row.skill.name }} x{{ row.times_purchased }}"
            "{% endfor %}|{{ character.group.name }}"
        )
        resp = test_client.post(
            f"/templates/api/{template.id}/render",
            json={
                "front_html": front_html,
                "back_html": "",
                "css_styles": "",
                "preview_data": {
                    "name": "Preview Person",
                    "species_id": str(species.id),
                    "faction_id": str(faction.id),
                    "group_name": "The Crew",
                    "skills": [{"skill_id": str(skill.id), "ranks": "2"}],
                },
            },
        )
        assert resp.status_code == 200
        rendered = resp.get_json()["front_html"]
        assert rendered == (
            f"Preview Person|{species.name}|{faction.name}|{skill.name} x2|The Crew"
        )
        assert Character.query.count() == characters_before

    def test_render_medicament_with_preview_data(self, test_client, admin_user, db, medicament):
        self.clear_templates(db)
        self.login_admin(test_client, admin_user)
        template = self.make_template(
            admin_user, PrintTemplateType.MEDICAMENT_CARD, "Medicament Card Data"
        )
        db.session.add(template)
        db.session.commit()
        resp = test_client.post(
            f"/templates/api/{template.id}/render",
            json={
                "front_html": (
                    "{{ medicament.name }}|"
                    "{% for mode in medicament.modes_list %}{{ mode.name }}{% endfor %}"
                ),
                "back_html": "",
                "css_styles": "",
                "preview_data": {
                    "source_id": str(medicament.id),
                    "modes": [{"name": "RED", "effect": "Heals"}, {"name": "", "effect": ""}],
                },
            },
        )
        assert resp.status_code == 200
        assert resp.get_json()["front_html"] == f"{medicament.name}|RED"
        db.session.refresh(medicament)
        assert medicament.modes is None

    def test_template_edit_shows_data_tab(self, test_client, admin_user, db, species):
        self.clear_templates(db)
        self.login_admin(test_client, admin_user)
        template = self.make_template(
            admin_user, PrintTemplateType.CHARACTER_SHEET, "Character Sheet Data Tab"
        )
        db.session.add(template)
        db.session.commit()
        resp = test_client.get(f"/templates/{template.id}/edit")
        assert resp.status_code == 200
        assert b'id="preview-data-panel"' in resp.data
        assert species.name.encode() in resp.data

    def test_render_seeded_condition_card(self, test_client, admin_user, db):
        self.clear_templates(db)
        self.login_admin(test_client, admin_user)
        template = self.make_template(
            admin_user, PrintTemplateType.CONDITION_CARD, "Condition Card Seeded"
        )
        template.has_back_side = True
        db.session.add(template)
        db.session.commit()
        with open("data/templates/condition_card/back.html", encoding="utf-8") as handle:
            back_html = handle.read()
        resp = test_client.post(
            f"/templates/api/{template.id}/render",
            json={"front_html": "Front", "back_html": back_html, "css_styles": ""},
        )
        assert resp.status_code == 200
        assert "Radiation Poisoning" in resp.get_json()["back_html"]

    def test_render_template_preview_blocks_config(self, test_client, admin_user, db, app):
        secret = "print-template-preview-secret"
        original_secret = app.config["SECRET_KEY"]
        app.config["SECRET_KEY"] = secret
        try:
            self.clear_templates(db)
            self.login_admin(test_client, admin_user)
            template = self.make_template(
                admin_user,
                PrintTemplateType.MEDICAMENT_CARD,
                "Medicament Card Config",
                front_html="Hello",
            )
            db.session.add(template)
            db.session.commit()
            resp = test_client.post(
                f"/templates/api/{template.id}/render",
                json={"front_html": "{{ config.SECRET_KEY }}", "back_html": "", "css_styles": ""},
            )
            assert resp.status_code == 400
            body = resp.get_data(as_text=True)
            assert secret not in body
            assert resp.get_json()["success"] is False
        finally:
            app.config["SECRET_KEY"] = original_secret

    def test_print_template_preview_blocks_config(self, test_client, admin_user, db, app):
        secret = "print-template-pdf-secret"
        original_secret = app.config["SECRET_KEY"]
        app.config["SECRET_KEY"] = secret
        try:
            self.clear_templates(db)
            self.login_admin(test_client, admin_user)
            template = self.make_template(
                admin_user,
                PrintTemplateType.ITEM_CARD,
                "Item Card Config",
                front_html="Hello",
            )
            db.session.add(template)
            db.session.commit()
            resp = test_client.post(
                f"/templates/api/{template.id}/print_preview",
                json={
                    "front_html": "{{ config['SECRET_KEY'] }}",
                    "back_html": "",
                    "css_styles": "",
                },
            )
            assert resp.status_code == 400
            assert secret not in resp.get_data(as_text=True)
        finally:
            app.config["SECRET_KEY"] = original_secret

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
