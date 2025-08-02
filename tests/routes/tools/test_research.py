import uuid


def login_user(client, user):
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user.id)
        sess["_fresh"] = True


class TestResearchAccess:
    def test_research_list_unauthorized(self, test_client):
        response = test_client.get("/research/")
        assert response.status_code == 302  # Redirect to login

    def test_research_list_authorized(self, test_client, user_rules_team, db, app):
        """Test research list page for authorized users"""
        with app.app_context():
            from models.database.permissions import Role as RoleModel
            from models.extensions import db as flask_db
            from models.tools.user import User

            # Create a new role in the Flask app's session
            role = RoleModel.query.filter_by(name="rules_team").first()
            if not role:
                # Create the role if it doesn't exist
                role = RoleModel(name="rules_team", description="Test rules_team role")
                flask_db.session.add(role)
                flask_db.session.commit()

                # Add research permissions to the role
                from models.database.permissions import Permission

                research_permissions = ["research.create"]
                for perm_name in research_permissions:
                    permission = Permission.query.filter_by(name=perm_name).first()
                    if permission:
                        role.add_permission(permission)
                flask_db.session.commit()

            # Create a new user in the Flask app's session
            flask_user = User(
                email=user_rules_team.email,
                first_name=user_rules_team.first_name,
                surname=user_rules_team.surname,
                email_verified=True,
            )
            flask_user.set_password("password")
            flask_user.role = role
            flask_db.session.add(flask_user)
            flask_db.session.commit()

            # Set the session to use the Flask app's user
            with test_client.session_transaction() as sess:
                sess["_user_id"] = str(flask_user.id)
                sess["_fresh"] = True

        response = test_client.get("/research/")
        assert response.status_code == 200

    def test_basic_authentication(self, test_client, user_rules_team, db):
        """Test basic authentication without research routes"""
        with test_client.session_transaction() as sess:
            sess["_user_id"] = str(user_rules_team.id)
            sess["_fresh"] = True

        # Try accessing the index page to see if authentication works at all
        response = test_client.get("/")
        print(f"Index response status: {response.status_code}")

        # Try accessing a simple route that requires login but not email verification
        response = test_client.get("/characters/")
        print(f"Characters response status: {response.status_code}")

        assert response.status_code in [200, 302]  # Should either work or redirect, not 404

    def test_research_create_unauthorized(self, test_client):
        response = test_client.get("/research/create")
        assert response.status_code == 302  # Redirect to login

    def test_research_create_authorized(self, test_client, user_rules_team, db, app):
        """Test research create page for authorized users"""
        with app.app_context():
            from models.database.permissions import Role as RoleModel
            from models.extensions import db as flask_db
            from models.tools.user import User

            # Create a new role in the Flask app's session
            role = RoleModel.query.filter_by(name="rules_team").first()
            if not role:
                # Create the role if it doesn't exist
                role = RoleModel(name="rules_team", description="Test rules_team role")
                flask_db.session.add(role)
                flask_db.session.commit()

                # Add research permissions to the role
                from models.database.permissions import Permission

                research_permissions = ["research.create"]
                for perm_name in research_permissions:
                    permission = Permission.query.filter_by(name=perm_name).first()
                    if permission:
                        role.add_permission(permission)
                flask_db.session.commit()

            # Create a new user in the Flask app's session
            flask_user = User(
                email=user_rules_team.email,
                first_name=user_rules_team.first_name,
                surname=user_rules_team.surname,
                email_verified=True,
            )
            flask_user.set_password("password")
            flask_user.role = role
            flask_db.session.add(flask_user)
            flask_db.session.commit()

            # Set the session to use the Flask app's user
            with test_client.session_transaction() as sess:
                sess["_user_id"] = str(flask_user.id)
                sess["_fresh"] = True

        response = test_client.get("/research/create")
        assert response.status_code == 200


class TestResearchCRUD:
    def test_create_research_success(self, test_client, user_rules_team, db, app):
        """Test creating a research project successfully"""
        with app.app_context():
            from models.database.item_type import ItemType
            from models.database.permissions import Role as RoleModel
            from models.extensions import db as flask_db
            from models.tools.user import User

            # Create a new role in the Flask app's session
            role = RoleModel.query.filter_by(name="rules_team").first()
            if not role:
                # Create the role if it doesn't exist
                role = RoleModel(name="rules_team", description="Test rules_team role")
                flask_db.session.add(role)
                flask_db.session.commit()

                # Add research permissions to the role
                from models.database.permissions import Permission

                research_permissions = ["research.create"]
                for perm_name in research_permissions:
                    permission = Permission.query.filter_by(name=perm_name).first()
                    if permission:
                        role.add_permission(permission)
                flask_db.session.commit()

            # Create a new user in the Flask app's session
            flask_user = User(
                email=user_rules_team.email,
                first_name=user_rules_team.first_name,
                surname=user_rules_team.surname,
                email_verified=True,
            )
            flask_user.set_password("password")
            flask_user.role = role
            flask_db.session.add(flask_user)

            # Create an item_type in the Flask app's session
            unique_id = uuid.uuid4().hex
            item_type = ItemType(name=f"Test Item Type {unique_id}", id_prefix="IT")
            flask_db.session.add(item_type)
            flask_db.session.commit()

            # Get the item_type ID before it gets detached
            item_type_id = item_type.id

            # Set the session to use the Flask app's user
            with test_client.session_transaction() as sess:
                sess["_user_id"] = str(flask_user.id)
                sess["_fresh"] = True

        unique_name = f"Test Research {uuid.uuid4().hex[:8]}"
        response = test_client.post(
            "/research/create",
            data={
                "project_name": unique_name,
                "type": "invention",
                "description": "Test research description",
                "blueprint_id": str(item_type_id),
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert unique_name.encode() in response.data

    def test_create_artefact_research_new(self, test_client, user_rules_team, db, app):
        """Test creating artefact research with new blueprint"""
        with app.app_context():
            from models.database.item_type import ItemType
            from models.database.permissions import Role as RoleModel
            from models.extensions import db as flask_db
            from models.tools.user import User

            # Create a new role in the Flask app's session
            role = RoleModel.query.filter_by(name="rules_team").first()
            if not role:
                # Create the role if it doesn't exist
                role = RoleModel(name="rules_team", description="Test rules_team role")
                flask_db.session.add(role)
                flask_db.session.commit()

                # Add research permissions to the role
                from models.database.permissions import Permission

                research_permissions = ["research.create"]
                for perm_name in research_permissions:
                    permission = Permission.query.filter_by(name=perm_name).first()
                    if permission:
                        role.add_permission(permission)
                flask_db.session.commit()

            # Create a new user in the Flask app's session
            flask_user = User(
                email=user_rules_team.email,
                first_name=user_rules_team.first_name,
                surname=user_rules_team.surname,
                email_verified=True,
            )
            flask_user.set_password("password")
            flask_user.role = role
            flask_db.session.add(flask_user)

            # Create an item_type in the Flask app's session
            unique_id = uuid.uuid4().hex
            item_type = ItemType(name=f"Test Item Type {unique_id}", id_prefix="IT")
            flask_db.session.add(item_type)
            flask_db.session.commit()

            # Get the item_type ID before it gets detached
            item_type_id = item_type.id

            # Set the session to use the Flask app's user
            with test_client.session_transaction() as sess:
                sess["_user_id"] = str(flask_user.id)
                sess["_fresh"] = True

        unique_name = f"Test Artefact {uuid.uuid4().hex[:8]}"
        response = test_client.post(
            "/research/create",
            data={
                "project_name": unique_name,
                "type": "artefact",
                "description": "Test artefact research",
                "blueprint_id": str(item_type_id),
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert unique_name.encode() in response.data

    def test_create_artefact_research_existing(self, test_client, user_rules_team, db, app):
        """Test creating artefact research with existing item"""
        with app.app_context():
            from models.database.item import Item
            from models.database.item_blueprint import ItemBlueprint
            from models.database.item_type import ItemType
            from models.database.permissions import Role as RoleModel
            from models.extensions import db as flask_db
            from models.tools.user import User

            # Create a new role in the Flask app's session
            role = RoleModel.query.filter_by(name="rules_team").first()
            if not role:
                # Create the role if it doesn't exist
                role = RoleModel(name="rules_team", description="Test rules_team role")
                flask_db.session.add(role)
                flask_db.session.commit()

                # Add research permissions to the role
                from models.database.permissions import Permission

                research_permissions = ["research.create"]
                for perm_name in research_permissions:
                    permission = Permission.query.filter_by(name=perm_name).first()
                    if permission:
                        role.add_permission(permission)
                flask_db.session.commit()

            # Create a new user in the Flask app's session
            flask_user = User(
                email=user_rules_team.email,
                first_name=user_rules_team.first_name,
                surname=user_rules_team.surname,
                email_verified=True,
            )
            flask_user.set_password("password")
            flask_user.role = role
            flask_db.session.add(flask_user)

            # Create an item_type in the Flask app's session
            unique_id = uuid.uuid4().hex
            item_type = ItemType(name=f"Test Item Type {unique_id}", id_prefix="IT")
            flask_db.session.add(item_type)
            flask_db.session.commit()

            # Create an item_blueprint in the Flask app's session
            blueprint = ItemBlueprint(
                name=f"Test Blueprint {unique_id}",
                item_type_id=item_type.id,
                blueprint_id=1,
                base_cost=10,
            )
            flask_db.session.add(blueprint)
            flask_db.session.commit()

            # Create an item in the Flask app's session
            item = Item(
                blueprint_id=blueprint.id,
                item_id=1,
            )
            flask_db.session.add(item)
            flask_db.session.commit()

            # Get the item ID before it gets detached
            item_id = item.id

            # Set the session to use the Flask app's user
            with test_client.session_transaction() as sess:
                sess["_user_id"] = str(flask_user.id)
                sess["_fresh"] = True

        unique_name = f"Test Artefact {uuid.uuid4().hex[:8]}"
        response = test_client.post(
            "/research/create",
            data={
                "project_name": unique_name,
                "type": "artefact",
                "description": "Test artefact research",
                "item_id": str(item_id),
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert unique_name.encode() in response.data

    def test_edit_research_get(self, test_client, user_rules_team, db, app):
        """Test editing research project"""
        with app.app_context():
            from models.database.permissions import Role as RoleModel
            from models.extensions import db as flask_db
            from models.tools.research import Research
            from models.tools.user import User

            # Create a new role in the Flask app's session
            role = RoleModel.query.filter_by(name="rules_team").first()
            if not role:
                # Create the role if it doesn't exist
                role = RoleModel(name="rules_team", description="Test rules_team role")
                flask_db.session.add(role)
                flask_db.session.commit()

                # Add research permissions to the role
                from models.database.permissions import Permission

                research_permissions = ["research.create"]
                for perm_name in research_permissions:
                    permission = Permission.query.filter_by(name=perm_name).first()
                    if permission:
                        role.add_permission(permission)
                flask_db.session.commit()

            # Create a new user in the Flask app's session
            flask_user = User(
                email=user_rules_team.email,
                first_name=user_rules_team.first_name,
                surname=user_rules_team.surname,
                email_verified=True,
            )
            flask_user.set_password("password")
            flask_user.role = role
            flask_db.session.add(flask_user)

            # Create a research project in the Flask app's session
            research_project = Research(
                project_name="Test Project with Stage",
                type="artefact",
                description="A test research project with stages",
            )
            flask_db.session.add(research_project)
            flask_db.session.commit()

            # Create a research stage for the project
            from models.tools.research import ResearchStage

            stage = ResearchStage(
                research_id=research_project.id,
                stage_number=1,
                name="Initial Analysis",
                description="First stage of research",
            )
            flask_db.session.add(stage)
            flask_db.session.commit()

            # Get the research project ID before it gets detached
            research_project_id = research_project.id
            research_project_name = research_project.project_name

            # Set the session to use the Flask app's user
            with test_client.session_transaction() as sess:
                sess["_user_id"] = str(flask_user.id)
                sess["_fresh"] = True

        response = test_client.get(f"/research/{research_project_id}/edit")
        assert response.status_code == 200
        assert research_project_name.encode() in response.data


class TestResearchAPI:
    def test_api_blueprints(self, test_client, user_rules_team, db, app):
        """Test API for blueprints"""
        with app.app_context():
            from models.database.permissions import Role as RoleModel
            from models.extensions import db as flask_db
            from models.tools.user import User

            # Create a new role in the Flask app's session
            role = RoleModel.query.filter_by(name="rules_team").first()
            if not role:
                # Create the role if it doesn't exist
                role = RoleModel(name="rules_team", description="Test rules_team role")
                flask_db.session.add(role)
                flask_db.session.commit()

                # Add research permissions to the role
                from models.database.permissions import Permission

                research_permissions = ["research.create"]
                for perm_name in research_permissions:
                    permission = Permission.query.filter_by(name=perm_name).first()
                    if permission:
                        role.add_permission(permission)
                flask_db.session.commit()

            # Create a new user in the Flask app's session
            flask_user = User(
                email=user_rules_team.email,
                first_name=user_rules_team.first_name,
                surname=user_rules_team.surname,
                email_verified=True,
            )
            flask_user.set_password("password")
            flask_user.role = role
            flask_db.session.add(flask_user)
            flask_db.session.commit()

            # Set the session to use the Flask app's user
            with test_client.session_transaction() as sess:
                sess["_user_id"] = str(flask_user.id)
                sess["_fresh"] = True

        response = test_client.get("/research/api/blueprints")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) > 0

    def test_api_exotics(self, test_client, user_rules_team, db, app):
        """Test API for exotics"""
        with app.app_context():
            from models.database.permissions import Role as RoleModel
            from models.extensions import db as flask_db
            from models.tools.user import User

            # Create a new role in the Flask app's session
            role = RoleModel.query.filter_by(name="rules_team").first()
            if not role:
                # Create the role if it doesn't exist
                role = RoleModel(name="rules_team", description="Test rules_team role")
                flask_db.session.add(role)
                flask_db.session.commit()

                # Add research permissions to the role
                from models.database.permissions import Permission

                research_permissions = ["research.create"]
                for perm_name in research_permissions:
                    permission = Permission.query.filter_by(name=perm_name).first()
                    if permission:
                        role.add_permission(permission)
                flask_db.session.commit()

            # Create a new user in the Flask app's session
            flask_user = User(
                email=user_rules_team.email,
                first_name=user_rules_team.first_name,
                surname=user_rules_team.surname,
                email_verified=True,
            )
            flask_user.set_password("password")
            flask_user.role = role
            flask_db.session.add(flask_user)
            flask_db.session.commit()

            # Set the session to use the Flask app's user
            with test_client.session_transaction() as sess:
                sess["_user_id"] = str(flask_user.id)
                sess["_fresh"] = True

        response = test_client.get("/research/api/exotics")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) > 0


class TestResearchAssignees:
    def test_assignees_list(self, test_client, user_rules_team, db, app):
        """Test listing assignees for a research project"""
        with app.app_context():
            from models.database.permissions import Role as RoleModel
            from models.extensions import db as flask_db
            from models.tools.research import Research
            from models.tools.user import User

            # Create a new role in the Flask app's session
            role = RoleModel.query.filter_by(name="rules_team").first()
            if not role:
                # Create the role if it doesn't exist
                role = RoleModel(name="rules_team", description="Test rules_team role")
                flask_db.session.add(role)
                flask_db.session.commit()

                # Add research permissions to the role
                from models.database.permissions import Permission

                research_permissions = ["research.create"]
                for perm_name in research_permissions:
                    permission = Permission.query.filter_by(name=perm_name).first()
                    if permission:
                        role.add_permission(permission)
                flask_db.session.commit()

            # Create a new user in the Flask app's session
            flask_user = User(
                email=user_rules_team.email,
                first_name=user_rules_team.first_name,
                surname=user_rules_team.surname,
                email_verified=True,
            )
            flask_user.set_password("password")
            flask_user.role = role
            flask_db.session.add(flask_user)

            # Create a research project in the Flask app's session
            research_project = Research(
                project_name="Test Project with Stage",
                type="artefact",
                description="A test research project with stages",
            )
            flask_db.session.add(research_project)
            flask_db.session.commit()

            # Create a research stage for the project
            from models.tools.research import ResearchStage

            stage = ResearchStage(
                research_id=research_project.id,
                stage_number=1,
                name="Initial Analysis",
                description="First stage of research",
            )
            flask_db.session.add(stage)
            flask_db.session.commit()

            # Get the research project ID before it gets detached
            research_project_id = research_project.id

            # Set the session to use the Flask app's user
            with test_client.session_transaction() as sess:
                sess["_user_id"] = str(flask_user.id)
                sess["_fresh"] = True

        response = test_client.get(f"/research/{research_project_id}/assignees")
        assert response.status_code == 200

    def test_remove_assignee(
        self,
        test_client,
        user_rules_team,
        db,
        app,
    ):
        """Test removing an assignee from a research project"""
        with app.app_context():
            from models.database.faction import Faction
            from models.database.permissions import Role as RoleModel
            from models.database.species import Species
            from models.extensions import db as flask_db
            from models.tools.character import Character
            from models.tools.research import CharacterResearch, Research
            from models.tools.user import User

            # Create a new role in the Flask app's session
            role = RoleModel.query.filter_by(name="rules_team").first()
            if not role:
                # Create the role if it doesn't exist
                role = RoleModel(name="rules_team", description="Test rules_team role")
                flask_db.session.add(role)
                flask_db.session.commit()

                # Add research permissions to the role
                from models.database.permissions import Permission

                research_permissions = ["research.create"]
                for perm_name in research_permissions:
                    permission = Permission.query.filter_by(name=perm_name).first()
                    if permission:
                        role.add_permission(permission)
                flask_db.session.commit()

            # Create a new user in the Flask app's session
            flask_user = User(
                email=user_rules_team.email,
                first_name=user_rules_team.first_name,
                surname=user_rules_team.surname,
                email_verified=True,
            )
            flask_user.set_password("password")
            flask_user.role = role
            flask_db.session.add(flask_user)

            # Create a faction in the Flask app's session
            faction = Faction(name="Test Faction", wiki_slug="test-faction")
            flask_db.session.add(faction)
            flask_db.session.commit()

            # Create a species in the Flask app's session
            species = Species(
                name="Test Species",
                wiki_page="test-species",
                permitted_factions=f"[{faction.id}]",
                body_hits_type="locational",
                body_hits=5,
                death_count=3,
            )
            flask_db.session.add(species)
            flask_db.session.commit()

            # Create a character in the Flask app's session
            character = Character(
                user_id=flask_user.id, name="Test Character", species_id=species.id, status="active"
            )
            flask_db.session.add(character)
            flask_db.session.commit()

            # Create a research project in the Flask app's session
            research_project = Research(
                project_name="Test Project with Stage",
                type="artefact",
                description="A test research project with stages",
            )
            flask_db.session.add(research_project)
            flask_db.session.commit()

            # Create a research stage for the project
            from models.tools.research import ResearchStage

            stage = ResearchStage(
                research_id=research_project.id,
                stage_number=1,
                name="Initial Analysis",
                description="First stage of research",
            )
            flask_db.session.add(stage)
            flask_db.session.commit()

            # Create a character research in the Flask app's session
            character_research = CharacterResearch(
                character_id=character.id, research_id=research_project.id
            )
            flask_db.session.add(character_research)
            flask_db.session.commit()

            # Get the IDs before they get detached
            research_project_id = research_project.id
            character_research_id = character_research.id

            # Set the session to use the Flask app's user
            with test_client.session_transaction() as sess:
                sess["_user_id"] = str(flask_user.id)
                sess["_fresh"] = True

        response = test_client.post(
            f"/research/{research_project_id}/assignees/" f"{character_research_id}/remove",
            follow_redirects=True,
        )
        assert response.status_code == 200

    def test_edit_progress_get(
        self,
        test_client,
        user_rules_team,
        db,
        app,
    ):
        """Test editing progress for a research assignee"""
        with app.app_context():
            from models.database.faction import Faction
            from models.database.permissions import Role as RoleModel
            from models.database.species import Species
            from models.extensions import db as flask_db
            from models.tools.character import Character
            from models.tools.research import CharacterResearch, Research
            from models.tools.user import User

            # Create a new role in the Flask app's session
            role = RoleModel.query.filter_by(name="rules_team").first()
            if not role:
                # Create the role if it doesn't exist
                role = RoleModel(name="rules_team", description="Test rules_team role")
                flask_db.session.add(role)
                flask_db.session.commit()

                # Add research permissions to the role
                from models.database.permissions import Permission

                research_permissions = ["research.create"]
                for perm_name in research_permissions:
                    permission = Permission.query.filter_by(name=perm_name).first()
                    if permission:
                        role.add_permission(permission)
                flask_db.session.commit()

            # Create a new user in the Flask app's session
            flask_user = User(
                email=user_rules_team.email,
                first_name=user_rules_team.first_name,
                surname=user_rules_team.surname,
                email_verified=True,
            )
            flask_user.set_password("password")
            flask_user.role = role
            flask_db.session.add(flask_user)

            # Create a faction in the Flask app's session
            faction = Faction(name="Test Faction", wiki_slug="test-faction")
            flask_db.session.add(faction)
            flask_db.session.commit()

            # Create a species in the Flask app's session
            species = Species(
                name="Test Species",
                wiki_page="test-species",
                permitted_factions=f"[{faction.id}]",
                body_hits_type="locational",
                body_hits=5,
                death_count=3,
            )
            flask_db.session.add(species)
            flask_db.session.commit()

            # Create a character in the Flask app's session
            character = Character(
                user_id=flask_user.id, name="Test Character", species_id=species.id, status="active"
            )
            flask_db.session.add(character)
            flask_db.session.commit()

            # Create a research project in the Flask app's session
            research_project = Research(
                project_name="Test Project with Stage",
                type="artefact",
                description="A test research project with stages",
            )
            flask_db.session.add(research_project)
            flask_db.session.commit()

            # Create a research stage for the project
            from models.tools.research import ResearchStage

            stage = ResearchStage(
                research_id=research_project.id,
                stage_number=1,
                name="Initial Analysis",
                description="First stage of research",
            )
            flask_db.session.add(stage)
            flask_db.session.commit()

            # Create a character research in the Flask app's session
            character_research = CharacterResearch(
                character_id=character.id, research_id=research_project.id
            )
            flask_db.session.add(character_research)
            flask_db.session.commit()

            # Get the IDs before they get detached
            research_project_id = research_project.id
            character_research_id = character_research.id

            # Set the session to use the Flask app's user
            with test_client.session_transaction() as sess:
                sess["_user_id"] = str(flask_user.id)
                sess["_fresh"] = True

        response = test_client.get(
            f"/research/{research_project_id}/assignees/" f"{character_research_id}/progress"
        )
        assert response.status_code == 200


class TestResearchProjectInfo:
    def test_project_info_forbidden(
        self,
        test_client,
        regular_user,
        research_project_with_stage,
        character_with_faction,
    ):
        # Assign the research to the character owned by regular_user
        from models.tools.research import CharacterResearch, ResearchStage

        stage = ResearchStage.query.filter_by(research_id=research_project_with_stage.id).first()
        cr = CharacterResearch(
            character_id=character_with_faction.id,
            research_id=research_project_with_stage.id,
            current_stage_id=stage.id,
        )
        from models.extensions import db

        db.session.add(cr)
        db.session.commit()

        login_user(test_client, regular_user)
        response = test_client.get(f"/research/{research_project_with_stage.id}")
        assert response.status_code in (
            302,
            403,
            404,
        )  # Should not be accessible to regular users

    def test_project_info_not_found(self, test_client, regular_user):
        login_user(test_client, regular_user)
        response = test_client.get("/research/99999")
        assert response.status_code in (302, 403, 404)
