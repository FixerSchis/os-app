import pytest

from models.database.group_type import GroupType


class TestGroupTypeModel:
    def test_create_group_type(self, db):
        group_type = GroupType(
            name="TestType",
            description="A test group type",
            income_items_list=[1, 2, 3],
            income_items_discount=0.5,
            income_substances=True,
            income_substance_cost=10,
            income_medicaments=True,
            income_medicament_cost=5,
            income_distribution_dict={"items": 50, "chits": 50},
        )
        db.session.add(group_type)
        db.session.commit()
        assert group_type.id is not None
        assert group_type.income_items_list == [1, 2, 3]
        assert group_type.income_distribution_dict == {"items": 50, "chits": 50}

    def test_unique_name_constraint(self, db):
        group_type1 = GroupType(
            name="UniqueType",
            description="desc",
            income_items_list=[],
            income_items_discount=0.5,
            income_substances=False,
            income_substance_cost=0,
            income_medicaments=False,
            income_medicament_cost=0,
            income_distribution_dict={},
        )
        db.session.add(group_type1)
        db.session.commit()
        group_type2 = GroupType(
            name="UniqueType",
            description="desc2",
            income_items_list=[],
            income_items_discount=0.5,
            income_substances=False,
            income_substance_cost=0,
            income_medicaments=False,
            income_medicament_cost=0,
            income_distribution_dict={},
        )
        db.session.add(group_type2)
        with pytest.raises(Exception):
            db.session.commit()
        db.session.rollback()

    def test_income_items_list_property(self, db):
        group_type = GroupType(
            name="ListType",
            description="desc",
            income_items_list=[10, 20],
            income_items_discount=0.5,
            income_substances=False,
            income_substance_cost=0,
            income_medicaments=False,
            income_medicament_cost=0,
            income_distribution_dict={},
        )
        db.session.add(group_type)
        db.session.commit()
        # Test setter and getter
        group_type.income_items_list = [30, 40]
        db.session.commit()
        assert group_type.income_items_list == [30, 40]

    def test_income_distribution_dict_property(self, db):
        group_type = GroupType(
            name="DistType",
            description="desc",
            income_items_list=[],
            income_items_discount=0.5,
            income_substances=False,
            income_substance_cost=0,
            income_medicaments=False,
            income_medicament_cost=0,
            income_distribution_dict={"items": 60, "chits": 40},
        )
        db.session.add(group_type)
        db.session.commit()
        # Test setter and getter
        group_type.income_distribution_dict = {"items": 70, "chits": 30}
        db.session.commit()
        assert group_type.income_distribution_dict == {"items": 70, "chits": 30}
